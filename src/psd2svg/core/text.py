import dataclasses
import logging
import xml.etree.ElementTree as ET
from enum import IntEnum
from itertools import groupby
from typing import Any, Iterator

from psd_tools.api import layers
from psd_tools.psd.descriptor import RawData
from psd_tools.psd.engine_data import DictElement, EngineData
from psd_tools.psd.tagged_blocks import TypeToolObjectSetting
from psd_tools.terminology import Key

from psd2svg import svg_utils
from psd2svg.core import color_utils, font_utils
from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class TextWrappingMode(IntEnum):
    """Text wrapping mode values."""

    NONE = 0  # No wrapping, use native SVG <text> (current behavior)
    FOREIGN_OBJECT = 1  # Use <foreignObject> with XHTML for text wrapping


class Justification(IntEnum):
    """Text justification values from Photoshop."""

    LEFT = 0
    RIGHT = 1
    CENTER = 2
    JUSTIFY_LAST_LEFT = 3
    JUSTIFY_LAST_RIGHT = 4
    JUSTIFY_LAST_CENTER = 5
    JUSTIFY_ALL = 6


class ShapeType(IntEnum):
    """Text shape type values from Photoshop."""

    POINT = 0
    BOUNDING_BOX = 1


class WritingDirection(IntEnum):
    """Text writing direction values from Photoshop."""

    HORIZONTAL_TB = 0
    VERTICAL_RL = 2


class FontCaps(IntEnum):
    """Font capitalization style values from Photoshop."""

    NORMAL = 0
    SMALL_CAPS = 1
    ALL_CAPS = 2


class FontBaseline(IntEnum):
    """Font baseline values from Photoshop.

    In Photoshop, script scale is 0.583 and position is +/- 0.333 for superscript and subscript.
    """

    ROMAN = 0
    SUPERSCRIPT = 1
    SUBSCRIPT = 2


class TextConverter(ConverterProtocol):
    """Mixin for text layers."""

    def create_text_node(self, layer: layers.TypeLayer) -> ET.Element:
        """Create SVG text node from a TypeLayer."""
        text_setting = TypeSetting(layer._data)

        # Determine if we should use foreignObject
        # Only use for bounding box text when explicitly enabled
        use_foreign_object = (
            hasattr(self, "text_wrapping_mode")
            and self.text_wrapping_mode == TextWrappingMode.FOREIGN_OBJECT
            and text_setting.shape_type == ShapeType.BOUNDING_BOX
        )

        if use_foreign_object:
            return self._create_foreign_object_text(layer, text_setting)
        else:
            return self._create_native_svg_text(layer, text_setting)

    def _create_native_svg_text(
        self, layer: layers.TypeLayer, text_setting: "TypeSetting"
    ) -> ET.Element:
        """Create native SVG <text> element (current implementation).

        Args:
            layer: TypeLayer to convert.
            text_setting: TypeSetting object with text data.

        Returns:
            text element with nested tspan elements.
        """
        # Use native x, y attributes for translation-only transforms
        transform = text_setting.transform
        uses_native_positioning = transform.is_translation_only()

        paragraphs = list(text_setting)

        if uses_native_positioning:
            # Don't set x/y on parent - each tspan will have its own position
            text_node = self.create_node("text")
        else:
            # Use transform for non-translation transforms
            text_node = self.create_node(
                "text",
                transform=transform.to_svg_matrix(),
            )

        if text_setting.writing_direction == WritingDirection.VERTICAL_RL:
            svg_utils.set_attribute(text_node, "writing-mode", "vertical-rl")

        for i, paragraph in enumerate(paragraphs):
            paragraph_node = self._add_paragraph(
                text_setting,
                text_node,
                paragraph,
                first_paragraph=(i == 0),
                uses_native_positioning=uses_native_positioning,
            )
            for span in paragraph:
                self._add_text_span(text_setting, paragraph_node, span)

        svg_utils.merge_common_child_attributes(
            text_node, excludes={"x", "y", "dx", "dy", "transform"}
        )
        svg_utils.merge_consecutive_siblings(text_node)
        svg_utils.merge_singleton_children(text_node)
        svg_utils.merge_attribute_less_children(text_node)
        return text_node

    def _create_foreign_object_text(
        self, layer: layers.TypeLayer, text_setting: "TypeSetting"
    ) -> ET.Element:
        """Create <foreignObject> with XHTML content for text wrapping.

        This method creates a foreignObject element containing XHTML div/p/span
        elements with CSS styling. This enables proper text wrapping for bounding
        box text, which is not natively supported by SVG.

        Args:
            layer: TypeLayer to convert.
            text_setting: TypeSetting object with text data.

        Returns:
            foreignObject element containing XHTML content.

        Note:
            - Requires XHTML namespace for proper rendering
            - Supported by modern browsers (Chrome, Firefox, Safari, Edge)
            - Not supported by resvg/resvg-py or many other SVG renderers (PDF converters, design tools)
        """
        bounds = text_setting.box_bounds
        transform = text_setting.transform

        # Create foreignObject element with bounding box dimensions
        foreign_obj = self.create_node(
            "foreignObject",
            x=transform.tx + bounds.left,
            y=transform.ty + bounds.top,
            width=bounds.width,
            height=bounds.height,
        )

        # Apply non-translation transform if needed
        if not transform.is_translation_only():
            svg_utils.set_attribute(foreign_obj, "transform", transform.to_svg_matrix())

        # Create XHTML div container with proper namespace
        container_styles = self._get_foreign_object_container_styles(
            text_setting, bounds
        )
        div = svg_utils.create_xhtml_node(
            "div",
            parent=foreign_obj,
            style=svg_utils.styles_to_string(container_styles),
        )

        # Add paragraphs
        for paragraph in text_setting:
            self._add_foreign_object_paragraph(div, paragraph, text_setting)

        return foreign_obj

    def _add_paragraph(
        self,
        text_setting: "TypeSetting",
        text_node: ET.Element,
        paragraph: "Paragraph",
        first_paragraph: bool = False,
        uses_native_positioning: bool = False,
    ) -> ET.Element:
        """Add a paragraph to the text node."""
        line_height = paragraph.compute_leading()
        text_anchor = paragraph.get_text_anchor()

        # Calculate positioning based on shape type and writing direction
        x, y, dominant_baseline = self._compute_paragraph_position(
            text_setting, text_anchor
        )

        # Create paragraph node
        paragraph_node = self._create_paragraph_node(
            text_setting,
            text_node,
            x,
            y,
            line_height,
            text_anchor,
            dominant_baseline,
            first_paragraph,
            uses_native_positioning,
        )

        # Apply justification settings
        self._apply_justification(paragraph, paragraph_node, text_setting)

        return paragraph_node

    def _compute_paragraph_position(
        self,
        text_setting: "TypeSetting",
        text_anchor: str | None,
    ) -> tuple[float, float, str | None]:
        """Compute paragraph position based on justification, shape type, and writing direction.

        Args:
            text_setting: Type setting object containing bounds and writing direction.
            text_anchor: SVG text-anchor value ("start", "middle", "end", or None).

        Returns:
            Tuple of (x, y, dominant_baseline) for positioning the paragraph.
        """
        x = 0.0
        y = 0.0
        dominant_baseline = None

        if text_setting.shape_type == ShapeType.BOUNDING_BOX:
            dominant_baseline = "hanging"
            if text_setting.writing_direction == WritingDirection.HORIZONTAL_TB:
                if text_anchor == "end":
                    x = text_setting.bounds.right
                elif text_anchor == "middle":
                    x = (text_setting.bounds.left + text_setting.bounds.right) / 2
            elif text_setting.writing_direction == WritingDirection.VERTICAL_RL:
                logger.debug(
                    "Dominant baseline may not be supported by SVG renderers for vertical text."
                )
                x = text_setting.bounds.right
                if text_anchor == "end":
                    y = text_setting.bounds.bottom
                elif text_anchor == "middle":
                    y = (text_setting.bounds.top + text_setting.bounds.bottom) / 2

        return x, y, dominant_baseline

    def _create_paragraph_node(
        self,
        text_setting: "TypeSetting",
        text_node: ET.Element,
        x: float,
        y: float,
        line_height: float,
        text_anchor: str | None,
        dominant_baseline: str | None,
        first_paragraph: bool,
        uses_native_positioning: bool,
    ) -> ET.Element:
        """Create paragraph node with positioning attributes.

        All paragraphs use consistent structure: each tspan has explicit x/y or dy positioning.

        Args:
            text_setting: Type setting object containing transform information.
            text_node: Parent text element.
            x: Base x position.
            y: Base y position.
            line_height: Line height for dy attribute.
            text_anchor: SVG text-anchor value.
            dominant_baseline: SVG dominant-baseline value.
            first_paragraph: Whether this is the first paragraph.
            uses_native_positioning: Whether native x/y positioning is used.

        Returns:
            New tspan element with appropriate position attributes.
        """
        # Add transform offset if using native positioning
        if uses_native_positioning:
            transform = text_setting.transform
            x += transform.tx
            y += transform.ty

        # Determine if we should set x, y on the tspan
        # All paragraphs get x for consistency (to reset horizontal position)
        # First paragraph gets both x and y
        # Subsequent paragraphs get x and dy (for line spacing)
        if uses_native_positioning:
            should_set_x = True  # Always set x for consistency
            should_set_y = first_paragraph  # Only first paragraph gets y
        else:
            # Using transform positioning
            should_set_x = x != 0.0 or not first_paragraph
            should_set_y = y != 0.0 and first_paragraph

        # Create paragraph node
        # TODO: There is still a difference with PSD rendering on dominant-baseline.
        with self.set_current(text_node):
            return self.create_node(
                "tspan",
                text_anchor=text_anchor,
                x=x if should_set_x else None,
                y=y if should_set_y else None,
                dy=line_height if not first_paragraph else None,
                dominant_baseline=dominant_baseline,
            )

    def _apply_justification(
        self,
        paragraph: "Paragraph",
        paragraph_node: ET.Element,
        text_setting: "TypeSetting",
    ) -> None:
        """Apply justification settings to paragraph node.

        Args:
            paragraph: Paragraph object containing justification settings.
            paragraph_node: SVG tspan element to apply justification to.
            text_setting: Type setting object containing bounds information.
        """
        if paragraph.justification == Justification.JUSTIFY_ALL:
            logger.info("Justify All is not fully supported in SVG.")
            svg_utils.set_attribute(
                paragraph_node,
                "textLength",
                svg_utils.num2str(text_setting.bounds.width),
            )
            svg_utils.set_attribute(paragraph_node, "lengthAdjust", "spacingAndGlyphs")

    def _add_text_span(
        self, text_setting: "TypeSetting", paragraph_node: ET.Element, span: "Span"
    ) -> ET.Element:
        """Add a text span to the paragraph node."""
        style = span.style
        font_mapping = getattr(self, "font_mapping", None)
        enable_fontconfig = getattr(self, "enable_fontconfig", True)
        font_info = text_setting.get_font_info(
            style.font, font_mapping, enable_fontconfig
        )

        # Collect font info for later use in rasterization.
        if font_info and font_info.postscript_name not in self.fonts:
            self.fonts[font_info.postscript_name] = font_info

        # Determine font weight
        # Only set font-weight if it differs from regular (400)
        # SVG default is 400, so we only need to specify non-regular weights
        # Use numeric CSS weights for better compatibility
        font_weight: int | str | None = None
        if font_info:
            css_weight = font_info.css_weight
            # Apply faux bold if needed
            if style.faux_bold and css_weight < 700:
                css_weight = 700
            # Only set font-weight if not regular (400)
            if css_weight != 400:
                font_weight = css_weight
        elif style.faux_bold:
            font_weight = "bold"

        with self.set_current(paragraph_node):
            tspan = self.create_node(
                "tspan",
                text=span.text.strip("\r"),  # Remove carriage return characters
                font_size=style.font_size,
                font_family=font_info.family_name if font_info else None,
                font_weight=font_weight,
                font_style="italic"
                if (font_info and font_info.italic) or style.faux_italic
                else None,
                fill=style.get_fill_color(),
                stroke=style.get_stroke_color(),
                baseline_shift=style.baseline_shift
                if style.baseline_shift != 0.0
                else None,
            )
        if style.font_caps == FontCaps.ALL_CAPS:
            svg_utils.add_style(tspan, "text-transform", "uppercase")
        elif style.font_caps == FontCaps.SMALL_CAPS:
            # NOTE: Using text_settings.small_caps_size with text-transform may be more accurate.
            svg_utils.set_attribute(tspan, "font-variant", "small-caps")

        if style.underline:
            svg_utils.append_attribute(tspan, "text-decoration", "underline")
        if style.strikethrough:
            svg_utils.append_attribute(tspan, "text-decoration", "line-through")

        # NOTE: Photoshop uses different values for subscript position/size.
        # Using baseline-shift with sub or super will result in inaccurate rendering.
        if style.font_baseline == FontBaseline.SUPERSCRIPT:
            svg_utils.set_attribute(
                tspan,
                "baseline-shift",
                style.font_size * text_setting.superscript_position,
            )
            svg_utils.set_attribute(
                tspan, "font-size", style.font_size * text_setting.superscript_size
            )
        elif style.font_baseline == FontBaseline.SUBSCRIPT:
            svg_utils.set_attribute(
                tspan,
                "baseline-shift",
                -style.font_size * text_setting.subscript_position,
            )
            svg_utils.set_attribute(
                tspan, "font-size", style.font_size * text_setting.subscript_size
            )

        # Apply letter spacing from tracking, tsume, and optional global offset
        # NOTE: Tracking is in 1/1000 em units.
        # NOTE: Tsume is a percentage (0-1) that reduces spacing by that amount of font size.
        letter_spacing = style.tracking / 1000 * style.font_size
        letter_spacing -= style.tsume * style.font_size  # Tsume tightens spacing
        if hasattr(self, "text_letter_spacing_offset"):
            letter_spacing += self.text_letter_spacing_offset

        # Only set letter-spacing if non-zero (or if offset makes it non-zero)
        if letter_spacing != 0:
            svg_utils.set_attribute(
                tspan,
                "letter-spacing",
                svg_utils.num2str(letter_spacing),
            )

        # Apply kerning adjustment (manual kerning in 1/1000 em units)
        # Kerning adjusts the spacing BEFORE the current character (between previous and current).
        # We use dx/dy to shift the character position, which effectively adjusts the space before it.
        # NOTE: letter-spacing adds space AFTER characters, so we can't use it for kerning.
        if style.kerning != 0:
            kerning_offset = style.kerning / 1000 * style.font_size
            # Use dx for horizontal text, dy for vertical text
            if text_setting.writing_direction == WritingDirection.HORIZONTAL_TB:
                svg_utils.set_attribute(tspan, "dx", svg_utils.num2str(kerning_offset))
            elif text_setting.writing_direction == WritingDirection.VERTICAL_RL:
                svg_utils.set_attribute(tspan, "dy", svg_utils.num2str(kerning_offset))

        if style.vertical_scale != 1.0 or style.horizontal_scale != 1.0:
            # NOTE: Transform cannot be applied to tspan in SVG 1.1 but only in SVG 2.
            # Workaround would be to split tspan's into text nodes, but it's complex.
            # Singleton merge won't work as long as the text container has transform attribute,
            # which always happens here.
            logger.debug(
                "Applying scale transform to tspan is not supported in SVG 1.1."
            )
            svg_utils.append_attribute(
                tspan,
                "transform",
                "scale({},{})".format(
                    svg_utils.num2str(style.horizontal_scale),
                    svg_utils.num2str(style.vertical_scale),
                ),
            )

            # Set transform-origin to the paragraph's position to prevent scale from shifting the text
            # Get x and y from parent paragraph node
            parent_x = paragraph_node.attrib.get("x")
            parent_y = paragraph_node.attrib.get("y")
            if parent_x is not None and parent_y is not None:
                svg_utils.set_attribute(
                    tspan,
                    "transform-origin",
                    f"{parent_x} {parent_y}",
                )

        if (
            text_setting.writing_direction == WritingDirection.VERTICAL_RL
            and style.baseline_direction == 1
        ):
            # NOTE: Only Chromium-based browsers support 'text-orientation: upright' for SVG.
            logger.debug(
                "Applying text-orientation: upright, but may not be supported in SVG renderers."
            )
            svg_utils.add_style(tspan, "text-orientation", "upright")
            # NOTE: glyph-orientation-vertical is deprecated but may help with compatibility.
            # svg_utils.set_attribute(tspan, "glyph-orientation-vertical", "90")
        return tspan

    def _get_foreign_object_container_styles(
        self, text_setting: "TypeSetting", bounds: "Rectangle"
    ) -> dict[str, str]:
        """Get CSS styles for foreignObject container div.

        Args:
            text_setting: TypeSetting object with writing direction.
            bounds: Bounding box dimensions.

        Returns:
            Dictionary of CSS property names to values.
        """
        styles = {
            "width": f"{bounds.width}px",
            "height": f"{bounds.height}px",
            "margin": "0",
            "padding": "0",
            "overflow": "hidden",  # Match Photoshop clipping behavior
            "box-sizing": "border-box",
            "font-family": "sans-serif",  # Default fallback
        }

        if text_setting.writing_direction == WritingDirection.VERTICAL_RL:
            styles["writing-mode"] = "vertical-rl"

        return styles

    def _add_foreign_object_paragraph(
        self, container: ET.Element, paragraph: "Paragraph", text_setting: "TypeSetting"
    ) -> None:
        """Add a paragraph as XHTML <p> element.

        Args:
            container: Parent XHTML div element.
            paragraph: Paragraph object containing style and spans.
            text_setting: TypeSetting object for font info lookup.
        """
        # Get paragraph CSS styles
        p_styles = self._get_foreign_object_paragraph_styles(paragraph)

        # Create <p> element
        p_elem = svg_utils.create_xhtml_node(
            "p",
            parent=container,
            style=svg_utils.styles_to_string(p_styles),
        )

        # Add spans
        for span in paragraph:
            self._add_foreign_object_span(p_elem, span, text_setting)

    def _get_foreign_object_paragraph_styles(
        self, paragraph: "Paragraph"
    ) -> dict[str, str]:
        """Convert paragraph settings to CSS styles.

        Args:
            paragraph: Paragraph object containing justification and leading.

        Returns:
            Dictionary of CSS property names to values.
        """
        styles = {
            "margin": "0",
            "padding": "0",
        }

        # Text alignment mapping
        justification_map = {
            Justification.LEFT: "left",
            Justification.RIGHT: "right",
            Justification.CENTER: "center",
            Justification.JUSTIFY_LAST_LEFT: "justify",
            Justification.JUSTIFY_LAST_RIGHT: "justify",
            Justification.JUSTIFY_LAST_CENTER: "justify",
            Justification.JUSTIFY_ALL: "justify",
        }
        text_align = justification_map.get(paragraph.justification, "left")
        if text_align != "left":  # Skip default
            styles["text-align"] = text_align

        # Line height
        leading = paragraph.compute_leading()
        if leading > 0:
            styles["line-height"] = f"{leading}px"

        return styles

    def _add_foreign_object_span(
        self, p_elem: ET.Element, span: "Span", text_setting: "TypeSetting"
    ) -> None:
        """Add a text span as XHTML <span> element.

        Args:
            p_elem: Parent XHTML <p> element.
            span: Span object containing text and style.
            text_setting: TypeSetting object for font info lookup.
        """
        # Get span CSS styles
        span_styles = self._get_foreign_object_span_styles(span, text_setting)

        # Create <span> element
        # If no styles needed, add text directly to paragraph
        if not span_styles:
            # Append text to parent
            if len(p_elem) > 0:
                # Has children, append to last child's tail
                if p_elem[-1].tail:
                    p_elem[-1].tail += span.text.strip("\r")
                else:
                    p_elem[-1].tail = span.text.strip("\r")
            else:
                # No children, append to parent text
                if p_elem.text:
                    p_elem.text += span.text.strip("\r")
                else:
                    p_elem.text = span.text.strip("\r")
        else:
            svg_utils.create_xhtml_node(
                "span",
                parent=p_elem,
                text=span.text.strip("\r"),
                style=svg_utils.styles_to_string(span_styles),
            )

    def _get_foreign_object_span_styles(
        self, span: "Span", text_setting: "TypeSetting"
    ) -> dict[str, str]:
        """Convert span style settings to CSS styles.

        Args:
            span: Span object containing text style information.
            text_setting: TypeSetting object for font info and calculations.

        Returns:
            Dictionary of CSS property names to values.
        """
        style = span.style
        font_mapping = getattr(self, "font_mapping", None)
        enable_fontconfig = getattr(self, "enable_fontconfig", True)
        font_info = text_setting.get_font_info(
            style.font, font_mapping, enable_fontconfig
        )

        # Collect font info for later use in rasterization
        if font_info and font_info.postscript_name not in self.fonts:
            self.fonts[font_info.postscript_name] = font_info

        styles = {}

        # Font family
        if font_info:
            styles["font-family"] = f"'{font_info.family_name}'"

        # Font size
        if style.font_size:
            styles["font-size"] = f"{style.font_size}px"

        # Font weight
        if font_info:
            css_weight = font_info.css_weight
            if style.faux_bold and css_weight < 700:
                css_weight = 700
            if css_weight != 400:  # Skip default
                styles["font-weight"] = str(css_weight)
        elif style.faux_bold:
            styles["font-weight"] = "bold"

        # Font style
        if (font_info and font_info.italic) or style.faux_italic:
            styles["font-style"] = "italic"

        # Color
        fill_color = style.get_fill_color()
        if fill_color and fill_color != "none":
            styles["color"] = fill_color

        # Text decoration
        decorations = []
        if style.underline:
            decorations.append("underline")
        if style.strikethrough:
            decorations.append("line-through")
        if decorations:
            styles["text-decoration"] = " ".join(decorations)

        # Text transform
        if style.font_caps == FontCaps.ALL_CAPS:
            styles["text-transform"] = "uppercase"
        elif style.font_caps == FontCaps.SMALL_CAPS:
            styles["font-variant"] = "small-caps"

        # Letter spacing
        letter_spacing = style.tracking / 1000 * style.font_size
        if hasattr(self, "text_letter_spacing_offset"):
            letter_spacing += self.text_letter_spacing_offset
        if letter_spacing != 0:
            styles["letter-spacing"] = f"{letter_spacing}px"

        # Vertical alignment (superscript/subscript)
        if style.font_baseline == FontBaseline.SUPERSCRIPT:
            styles["vertical-align"] = "super"
            styles["font-size"] = f"{style.font_size * text_setting.superscript_size}px"
        elif style.font_baseline == FontBaseline.SUBSCRIPT:
            styles["vertical-align"] = "sub"
            styles["font-size"] = f"{style.font_size * text_setting.subscript_size}px"
        elif style.baseline_shift != 0.0:
            # Custom baseline shift
            styles["vertical-align"] = f"{style.baseline_shift}px"

        # Horizontal/vertical scale
        if style.vertical_scale != 1.0 or style.horizontal_scale != 1.0:
            styles["transform"] = (
                f"scale({style.horizontal_scale}, {style.vertical_scale})"
            )
            styles["display"] = (
                "inline-block"  # Required for transform on inline elements
            )
            styles["transform-origin"] = "center"

        # Stroke (text outline) - CSS supports this with -webkit-text-stroke
        stroke_color = style.get_stroke_color()
        if stroke_color and stroke_color != "none":
            # Note: This is a webkit-specific property but widely supported
            styles["-webkit-text-stroke"] = f"1px {stroke_color}"

        return styles


@dataclasses.dataclass
class Paragraph:
    """Paragraph of text with associated style."""

    style: "ParagraphSheet"
    spans: list["Span"]

    def __iter__(self) -> Iterator["Span"]:
        """Iterate over spans."""
        return iter(self.spans)

    @property
    def justification(self) -> Justification:
        """Get justification value from paragraph style."""
        return Justification(self.style.justification)

    def get_text_anchor(self) -> str | None:
        """Get SVG text-anchor value based on justification."""
        mapping = {
            Justification.LEFT: None,  # Start is default
            Justification.RIGHT: "end",
            Justification.CENTER: "middle",
            Justification.JUSTIFY_LAST_LEFT: None,  # Start is default
            Justification.JUSTIFY_LAST_RIGHT: "end",
            Justification.JUSTIFY_LAST_CENTER: "middle",
            Justification.JUSTIFY_ALL: None,  # Justify all does not map to text-anchor
        }
        return mapping.get(self.justification, None)

    def compute_leading(self) -> float:
        """Compute leading value for the paragraph."""
        return max(
            span.style.compute_leading(self.style.auto_leading) for span in self.spans
        )


@dataclasses.dataclass
class Span:
    """Span of text with associated style."""

    start: int
    end: int
    text: str
    style: "StyleSheet"


@dataclasses.dataclass
class Transform:
    """Affine transform matrix."""

    xx: float
    yx: float
    xy: float
    yy: float
    tx: float
    ty: float

    def to_svg_matrix(self) -> str | None:
        """Convert to SVG matrix string."""
        if (self.xx, self.yx, self.xy, self.yy) == (1.0, 0.0, 0.0, 1.0):
            if (self.tx, self.ty) == (0.0, 0.0):
                return None  # Identity transform
            return "translate({})".format(svg_utils.seq2str((self.tx, self.ty)))
        return "matrix({})".format(
            svg_utils.seq2str((self.xx, self.yx, self.xy, self.yy, self.tx, self.ty))
        )

    def is_translation_only(self, tolerance: float = 1e-6) -> bool:
        """Check if the transform is only a translation.

        Args:
            tolerance: Maximum allowed deviation from identity matrix values.
                       Defaults to 1e-6 to account for floating-point precision.

        Returns:
            True if the transform is a translation (rotation/scale components form identity matrix).
        """
        return (
            abs(self.xx - 1.0) < tolerance
            and abs(self.yx - 0.0) < tolerance
            and abs(self.xy - 0.0) < tolerance
            and abs(self.yy - 1.0) < tolerance
        )


@dataclasses.dataclass
class Rectangle:
    """Rectangle data."""

    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        """Get width of the rectangle."""
        return self.right - self.left

    @property
    def height(self) -> float:
        """Get height of the rectangle."""
        return self.bottom - self.top


@dataclasses.dataclass
class ParagraphSheet:
    """Paragraph sheet data."""

    name: str
    default_style_sheet: int
    properties: dict

    @classmethod
    def from_dict(cls, data: dict) -> "ParagraphSheet":
        if "ParagraphSheet" in data:
            data = data["ParagraphSheet"]
        return cls(
            name=data.get("Name", ""),
            default_style_sheet=data.get("DefaultStyleSheet", 0),
            properties=dict(data.get("Properties", {})),
        )

    def __getitem__(self, key: str) -> Any:
        return self.properties.get(key)

    def get(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)

    @property
    def justification(self) -> Justification:
        """Get justification value."""
        return Justification(self.properties.get("Justification", 0))

    @property
    def first_line_indent(self) -> float:
        """Get first line indent value."""
        return float(self.properties.get("FirstLineIndent", 0.0))

    @property
    def start_indent(self) -> float:
        """Get start indent value."""
        return float(self.properties.get("StartIndent", 0.0))

    @property
    def end_indent(self) -> float:
        """Get end indent value."""
        return float(self.properties.get("EndIndent", 0.0))

    @property
    def space_before(self) -> float:
        """Get space before value."""
        return float(self.properties.get("SpaceBefore", 0.0))

    @property
    def space_after(self) -> float:
        """Get space after value."""
        return float(self.properties.get("SpaceAfter", 0.0))

    @property
    def auto_hyphenate(self) -> bool:
        """Whether auto hyphenation is enabled."""
        return bool(self.properties.get("AutoHyphenate", False))

    @property
    def hyphenation_word_size(self) -> int:
        """Get hyphenation word size."""
        return int(self.properties.get("HyphenationWordSize", 6))

    @property
    def pre_hyphen(self) -> int:
        """Get pre-hyphen characters count."""
        return int(self.properties.get("PreHyphen", 2))

    @property
    def post_hyphen(self) -> int:
        """Get post-hyphen characters count."""
        return int(self.properties.get("PostHyphen", 2))

    @property
    def consecutive_hyphens(self) -> int:
        """Get consecutive hyphens limit."""
        return int(self.properties.get("ConsecutiveHyphens", 8))

    @property
    def zone(self) -> float:
        """Get zone value."""
        return float(self.properties.get("Zone", 36.0))

    @property
    def word_spacing(self) -> tuple[float, float, float]:
        """Get word spacing as (min, desired, max)."""
        ws = self.properties.get("WordSpacing", [1.0, 1.0, 2.0])
        return (float(ws[0]), float(ws[1]), float(ws[2]))

    @property
    def letter_spacing(self) -> tuple[float, float, float]:
        """Get letter spacing as (min, desired, max)."""
        ls = self.properties.get("LetterSpacing", [0.0, 0.0, 0.05])
        return (float(ls[0]), float(ls[1]), float(ls[2]))

    @property
    def glyph_spacing(self) -> tuple[float, float, float]:
        """Get glyph spacing as (min, desired, max)."""
        gs = self.properties.get("GlyphSpacing", [1.0, 1.0, 1.0])
        return (float(gs[0]), float(gs[1]), float(gs[2]))

    @property
    def auto_leading(self) -> float:
        """Auto leading scale."""
        return float(self.properties.get("AutoLeading", 1.2))

    @property
    def leading_type(self) -> int:
        """Get leading type value."""
        return int(self.properties.get("LeadingType", 0))

    @property
    def hanging(self) -> bool:
        """Whether hanging punctuation is enabled."""
        return bool(self.properties.get("Hanging", False))

    @property
    def kinsoku_order(self) -> int:
        """Get kinsoku order value."""
        return int(self.properties.get("KinsokuOrder", 0))

    @property
    def every_line_composer(self) -> bool:
        """Whether every line composer is enabled."""
        return bool(self.properties.get("EveryLineComposer", False))


@dataclasses.dataclass
class StyleSheet:
    """Style sheet data."""

    name: str
    style_sheet_data: dict

    @classmethod
    def from_dict(cls, data: dict) -> "StyleSheet":
        if "StyleSheet" in data:
            data = data["StyleSheet"]
        return cls(
            name=data.get("Name", ""),
            style_sheet_data=dict(data.get("StyleSheetData", {})),
        )

    def __getitem__(self, key: str) -> Any:
        return self.style_sheet_data.get(key)

    def get(self, key: str, default: Any = None) -> Any:
        return self.style_sheet_data.get(key, default)

    @property
    def font(self) -> int:
        """Get font index."""
        return int(self.style_sheet_data.get("Font", 0))

    @property
    def font_size(self) -> float:
        """Get font size value."""
        return float(self.style_sheet_data.get("FontSize", 12.0))

    @property
    def faux_bold(self) -> bool:
        """Whether faux bold is enabled."""
        return bool(self.style_sheet_data.get("FauxBold", False))

    @property
    def faux_italic(self) -> bool:
        """Whether faux italic is enabled."""
        return bool(self.style_sheet_data.get("FauxItalic", False))

    @property
    def auto_leading(self) -> bool:
        """Whether auto leading is enabled."""
        return bool(self.style_sheet_data.get("AutoLeading", True))

    @property
    def leading(self) -> float:
        """Get leading value."""
        return float(self.style_sheet_data.get("Leading", 0.0))

    @property
    def horizontal_scale(self) -> float:
        """Get horizontal scale value in the range (0.0, 1.0)."""
        return float(self.style_sheet_data.get("HorizontalScale", 1.0))

    @property
    def vertical_scale(self) -> float:
        """Get vertical scale value in the range (0.0, 1.0)."""
        return float(self.style_sheet_data.get("VerticalScale", 1.0))

    @property
    def tracking(self) -> int:
        """Get tracking value."""
        return int(self.style_sheet_data.get("Tracking", 0))

    @property
    def auto_kerning(self) -> bool:
        """Whether auto kerning is enabled."""
        return bool(self.style_sheet_data.get("AutoKern", True))

    @property
    def kerning(self) -> int:
        """Get kerning value."""
        return int(self.style_sheet_data.get("Kerning", 0))

    @property
    def baseline_shift(self) -> float:
        """Get baseline shift value."""
        return float(self.style_sheet_data.get("BaselineShift", 0.0))

    @property
    def font_caps(self) -> FontCaps:
        """Get font capitalization style."""
        return FontCaps(self.style_sheet_data.get("FontCaps", 0))

    @property
    def font_baseline(self) -> FontBaseline:
        """Font baseline."""
        return FontBaseline(self.style_sheet_data.get("FontBaseline", 0))

    @property
    def underline(self) -> bool:
        """Whether underline is enabled."""
        return bool(self.style_sheet_data.get("Underline", False))

    @property
    def strikethrough(self) -> bool:
        """Whether strikethrough is enabled."""
        return bool(self.style_sheet_data.get("Strikethrough", False))

    @property
    def ligatures(self) -> bool:
        """Whether ligatures are enabled."""
        return bool(self.style_sheet_data.get("Ligatures", False))

    @property
    def discretionary_ligatures(self) -> bool:
        """Whether discretionary ligatures are enabled."""
        return bool(self.style_sheet_data.get("DLigatures", False))

    @property
    def baseline_direction(self) -> int:
        """Get baseline direction value."""
        return int(self.style_sheet_data.get("BaselineDirection", 0))

    @property
    def no_break(self) -> bool:
        """Whether no-break is enabled."""
        return bool(self.style_sheet_data.get("NoBreak", False))

    @property
    def tsume(self) -> float:
        """Get tsume (character tightening) value with values between 0 (no tightening) and 1 (maximum tightening).

        This is an East-Asian typography feature.
        """
        return float(self.style_sheet_data.get("Tsume", 0.0))

    @property
    def fill_color(self) -> tuple[float, float, float, float]:
        """Get fill color as ARGB tuple with values between 0 and 1."""
        color = self.style_sheet_data.get("FillColor", None)
        if color is None:
            return (1.0, 0.0, 0.0, 0.0)  # Default black
        assert "Type" in color and color["Type"].value == 1  # ARGB color
        return tuple(color["Values"])

    @property
    def stroke_color(self) -> tuple[float, float, float, float]:
        """Get stroke color as ARGB tuple with values between 0 and 1."""
        color = self.style_sheet_data.get("StrokeColor", None)
        if color is None:
            return (0.0, 0.0, 0.0, 0.0)  # Default transparent
        assert "Type" in color and color["Type"].value == 1  # ARGB color
        return tuple(color["Values"])

    @property
    def fill_flag(self) -> bool:
        """Whether fill is enabled."""
        return bool(self.style_sheet_data.get("FillFlag", True))

    @property
    def stroke_flag(self) -> bool:
        """Whether stroke is enabled."""
        return bool(self.style_sheet_data.get("StrokeFlag", False))

    def get_fill_color(self) -> str | None:
        """Get fill color as hex string."""
        if not self.fill_flag:
            return None
        return _get_hex_color_from_argb(self.fill_color)

    def get_stroke_color(self) -> str | None:
        """Get stroke color as hex string."""
        if not self.stroke_flag:
            return None
        return _get_hex_color_from_argb(self.stroke_color)

    def compute_leading(self, auto_leading_scale: float = 1.2) -> float:
        """Compute leading value."""
        if self.auto_leading:
            return self.font_size * auto_leading_scale
        return self.leading


class RunLengthIndex:
    """Get run index from character index using run length array.

    Example::

        rli = RunLengthIndex([4, 2, 5])
        rli(0) -> 0
        rli(3) -> 0
        rli(4) -> 1
        rli(5) -> 1
        rli(6) -> 2
        rli(10) -> 2
    """

    def __init__(self, run_length_array: list[int]):
        self._run_length_array = run_length_array
        self._cumulative_lengths = []
        cumulative = 0
        for length in run_length_array:
            cumulative += length
            self._cumulative_lengths.append(cumulative)

    @property
    def boundaries(self) -> list[int]:
        """Get the boundaries array."""
        return self._cumulative_lengths

    def __call__(self, index: int) -> int:
        """Get the run index for the given character index."""
        if index < 0:
            raise IndexError("Character index cannot be negative.")
        for run_index, cumulative_length in enumerate(self._cumulative_lengths):
            if index < cumulative_length:
                return run_index
        raise IndexError("Character index out of range.")


class TypeSetting:
    """Type tool object setting wrapper.

    Example::

        setting = TypeSetting(type_tool_object_setting)
        for span in setting:
            print(span.start, span.end, span.text, span.paragraph, span.style)
    """

    def __init__(self, setting: TypeToolObjectSetting):
        assert isinstance(setting, TypeToolObjectSetting)
        self._setting = setting

        assert "EngineData" in self._setting.text_data
        raw_data = self._setting.text_data["EngineData"]
        assert isinstance(raw_data, RawData)
        self._engine_data: EngineData = raw_data.value  # type: ignore

    @property
    def transform(self) -> Transform:
        """Affine transform matrix."""
        return Transform(*self._setting.transform)

    @property
    def bounds(self) -> Rectangle:
        """Text bounds rectangle.

        This is a user-defined bounds that may differ from the bounding box.
        Use bounds for positioning the text content by justification settings.
        """
        desc = self._setting.text_data.get("bounds")
        if not desc:
            logger.debug("Bounds not found in text data.")
            return Rectangle(0.0, 0.0, 0.0, 0.0)
        return Rectangle(
            left=float(desc[Key.Left].value),
            top=float(desc[Key.Top].value),
            right=float(desc[Key.Right].value),
            bottom=float(desc[Key.Bottom].value),
        )

    @property
    def bounding_box(self) -> Rectangle:
        """Text bounding box rectangle.

        This is a bounding box around the text content.
        """
        desc = self._setting.text_data.get("boundingBox")
        if not desc:
            logger.debug("Bounding box not found in text data.")
            return Rectangle(0.0, 0.0, 0.0, 0.0)
        return Rectangle(
            left=float(desc[Key.Left].value),
            top=float(desc[Key.Top].value),
            right=float(desc[Key.Right].value),
            bottom=float(desc[Key.Bottom].value),
        )

    @property
    def engine_data(self) -> EngineData:
        """Engine data dictionary."""
        return self._engine_data

    @property
    def resources(self) -> DictElement:
        """Resource dictionary from engine data."""
        assert "ResourceDict" in self.engine_data
        return self.engine_data["ResourceDict"]

    @property
    def document_resources(self) -> DictElement:
        """Document resource dictionary from engine data."""
        assert "DocumentResources" in self.engine_data
        return self.engine_data["DocumentResources"]

    @property
    def font_set(self) -> list[dict]:
        """List of font info dictionaries from resources."""
        return [dict(fs) for fs in self.resources.get("FontSet", [])]

    @property
    def paragraph_sheets(self) -> list[ParagraphSheet]:
        """List of paragraph sheets from resources."""
        return [
            ParagraphSheet(
                name=ps.get("Name", ""),
                default_style_sheet=ps.get("DefaultStyleSheet", 0),
                properties=dict(ps.get("Properties", {})),
            )
            for ps in self.resources.get("ParagraphSheetSet", [])
        ]

    @property
    def style_sheets(self) -> list[StyleSheet]:
        """List of style sheets from resources."""
        return [
            StyleSheet(
                name=ss.get("Name", ""),
                style_sheet_data=dict(ss.get("StyleSheetData", {})),
            )
            for ss in self.resources.get("StyleSheetSet", [])
        ]

    @property
    def engine_dict(self) -> DictElement:
        """Engine dictionary from engine data."""
        assert "EngineDict" in self.engine_data
        return self.engine_data["EngineDict"]

    @property
    def text(self) -> str:
        """Text content from engine data."""
        assert "Editor" in self.engine_dict
        assert "Text" in self.engine_dict["Editor"]
        return str(self.engine_dict["Editor"]["Text"].value)

    @property
    def _shapes(self) -> list[DictElement]:
        """Shapes dictionary from engine data."""
        assert "Rendered" in self.engine_dict
        rendered = self.engine_dict["Rendered"]
        assert "Shapes" in rendered
        return list(rendered["Shapes"]["Children"])

    @property
    def _shape(self) -> DictElement | None:
        """First shape dictionary from engine data."""
        shapes = self._shapes
        if not shapes:
            logger.debug("No shapes found.")
            return None
        elif len(shapes) > 1:
            logger.debug("Multiple shapes found, using the first one.")
        return shapes[0]

    @property
    def shape_type(self) -> ShapeType:
        """Shape type from engine data."""
        shape = self._shape
        assert shape is not None
        assert "ShapeType" in shape
        return ShapeType(shape["ShapeType"].value)

    @property
    def writing_direction(self) -> WritingDirection:
        """Writing direction from engine data.

        Values are:
        - 0: Horizontal Top to Bottom
        - 2: Vertical Right to Left

        TODO: There could be other values, need to verify.
        """
        assert "Rendered" in self.engine_dict
        rendered = self.engine_dict["Rendered"]
        assert "Shapes" in rendered
        assert "WritingDirection" in rendered["Shapes"]
        return WritingDirection(rendered["Shapes"]["WritingDirection"].value)

    @property
    def point_base(self) -> tuple[float, float]:
        """Point base from shape structure in engine data."""
        if self.shape_type != ShapeType.POINT:
            return (0.0, 0.0)  # Not a point shape
        shape = self._shape
        assert shape is not None
        assert "Cookie" in shape
        assert "Photoshop" in shape["Cookie"]
        assert "PointBase" in shape["Cookie"]["Photoshop"]
        point_base = shape["Cookie"]["Photoshop"]["PointBase"]
        return (point_base[0].value, point_base[1].value)

    @property
    def box_bounds(self) -> Rectangle:
        """Box bounds from shape structure in engine data."""
        if self.shape_type != ShapeType.BOUNDING_BOX:
            return Rectangle(0, 0, 0, 0)  # Not a bounding box shape
        shape = self._shape
        assert shape is not None
        assert "Cookie" in shape
        assert "Photoshop" in shape["Cookie"]
        assert "BoxBounds" in shape["Cookie"]["Photoshop"]
        bounds = shape["Cookie"]["Photoshop"]["BoxBounds"]
        return Rectangle(
            left=float(bounds[0].value),
            top=float(bounds[1].value),
            right=float(bounds[2].value),
            bottom=float(bounds[3].value),
        )

    @property
    def superscript_size(self) -> float:
        """Superscript size from document resources."""
        assert "SuperscriptSize" in self.document_resources
        return float(self.document_resources["SuperscriptSize"].value)

    @property
    def subscript_size(self) -> float:
        """Subscript size from document resources."""
        assert "SubscriptSize" in self.document_resources
        return float(self.document_resources["SubscriptSize"].value)

    @property
    def superscript_position(self) -> float:
        """Superscript position from document resources."""
        assert "SuperscriptPosition" in self.document_resources
        return float(self.document_resources["SuperscriptPosition"].value)

    @property
    def subscript_position(self) -> float:
        """Subscript position from document resources."""
        assert "SubscriptPosition" in self.document_resources
        return float(self.document_resources["SubscriptPosition"].value)

    @property
    def small_cap_size(self) -> float:
        """Small cap size from document resources."""
        assert "SmallCapSize" in self.document_resources
        return float(self.document_resources["SmallCapSize"].value)

    @property
    def _paragraph_run(self) -> DictElement:
        """Paragraph run dictionary from engine data."""
        assert "ParagraphRun" in self.engine_dict
        return self.engine_dict["ParagraphRun"]

    @property
    def _style_run(self) -> DictElement:
        """Style run dictionary from engine data."""
        assert "StyleRun" in self.engine_dict
        return self.engine_dict["StyleRun"]

    def __iter__(self) -> Iterator[Paragraph]:
        """Iterate over paragraph and style runs."""
        paragraph_index = RunLengthIndex(self._paragraph_run["RunLengthArray"])
        style_index = RunLengthIndex(self._style_run["RunLengthArray"])
        stops = sorted(set(paragraph_index.boundaries) | set(style_index.boundaries))
        for index, group in groupby(
            zip([0] + stops, stops), key=lambda start_end: paragraph_index(start_end[0])
        ):
            paragraph_sheet = self.get_paragraph_sheet(
                ParagraphSheet.from_dict(self._paragraph_run["RunArray"][index])
            )
            spans = [
                Span(
                    start=start,
                    end=stop,
                    text=str(self.text[start:stop]),
                    style=self.get_style_sheet(
                        StyleSheet.from_dict(
                            self._style_run["RunArray"][style_index(start)]
                        )
                    ),
                )
                for start, stop in group
            ]
            yield Paragraph(style=paragraph_sheet, spans=spans)

    def get_font_info(
        self,
        font_index: int,
        font_mapping: dict[str, dict[str, float | str]] | None = None,
        enable_fontconfig: bool = True,
    ) -> font_utils.FontInfo | None:
        """Get the font family name for the given font index.

        Args:
            font_index: Index into the font set.
            font_mapping: Optional custom font mapping dictionary.
            enable_fontconfig: If True, fall back to fontconfig for fonts not in
                              static mapping. If False, only use static/custom mapping.
                              Default: True.

        Returns:
            FontInfo object with font metadata, or None if font not found.
        """
        font_info = self.font_set[font_index]
        postscriptname = font_info.get("Name", None)
        if postscriptname is None:
            logger.warning(f"PostScript name not found for font index {font_index}.")
            return None
        return font_utils.FontInfo.find(
            postscriptname.value, font_mapping, enable_fontconfig
        )

    def get_paragraph_sheet(self, sheet: ParagraphSheet) -> ParagraphSheet:
        """Get the merged paragraph sheet."""
        default_properties = dict(
            self.paragraph_sheets[sheet.default_style_sheet].properties
        )
        default_properties.update(sheet.properties)
        return ParagraphSheet(
            name=sheet.name,
            default_style_sheet=sheet.default_style_sheet,
            properties=default_properties,
        )

    def get_style_sheet(self, sheet: StyleSheet) -> StyleSheet:
        """Get the merged style sheet."""
        default_sheet_data = dict(
            self.style_sheets[
                int(self.resources["TheNormalStyleSheet"])
            ].style_sheet_data
        )
        default_sheet_data.update(sheet.style_sheet_data)
        return StyleSheet(
            name=sheet.name,
            style_sheet_data=default_sheet_data,
        )


def _get_hex_color_from_argb(argb: tuple[float, float, float, float]) -> str | None:
    """Convert ARGB color tuple to hex string."""
    a, r, g, b = argb
    if a == 0:
        return "none"
    elif ((r, g, b) == (0, 0, 0)) and (a == 1):
        return None  # Default black color in SVG.
    r_int = int(r * 255)
    g_int = int(g * 255)
    b_int = int(b * 255)
    return color_utils.rgba2hex((r_int, g_int, b_int), alpha=a)
