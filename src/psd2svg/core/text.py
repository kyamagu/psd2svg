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

    def add_type(self, layer: layers.TypeLayer, **attrib: str) -> ET.Element | None:
        """Add a type layer to the svg document."""
        if not self.enable_text:
            return self.add_pixel(layer, **attrib)

        text_setting = TypeSetting(layer._data)
        return self._create_text_node(text_setting)

    def _create_text_node(self, text_setting: "TypeSetting") -> ET.Element:
        """Create SVG text node from type setting."""
        # Use native x, y attributes for translation-only transforms
        transform = text_setting.transform
        uses_native_positioning = transform.is_translation_only()

        # Check if all paragraphs have the same text-anchor value
        # Only enable native positioning optimization for first paragraph if they do
        paragraphs = list(text_setting)
        text_anchors = [p.get_text_anchor() for p in paragraphs]
        all_same_text_anchor = len(set(text_anchors)) == 1
        can_hoist_first_paragraph = uses_native_positioning and all_same_text_anchor

        if uses_native_positioning:
            text_node = self.create_node(
                "text",
                x=transform.tx if transform.tx != 0.0 else None,
                y=transform.ty if transform.ty != 0.0 else None,
            )
        else:
            text_node = self.create_node(
                "text",
                transform=transform.to_svg_matrix(),
            )

        if text_setting.writing_direction == WritingDirection.VERTICAL_RL:
            svg_utils.set_attribute(text_node, "writing-mode", "vertical-rl")
        # TODO: Support text wrapping when ShapeType is 1 (Bounding box).
        # TODO: Support adjustments.
        for i, paragraph in enumerate(paragraphs):
            paragraph_node = self._add_paragraph(
                text_setting,
                text_node,
                paragraph,
                first_paragraph=(i == 0),
                uses_native_positioning=uses_native_positioning,
                can_hoist_first_paragraph=can_hoist_first_paragraph,
            )
            for span in paragraph:
                self._add_text_span(text_setting, paragraph_node, span)

        self._merge_common_child_attributes(
            text_node, excludes={"x", "y", "dx", "dy", "transform"}
        )
        self._merge_singleton_children(text_node)
        self._merge_attribute_less_children(text_node)
        return text_node

    def _add_paragraph(
        self,
        text_setting: "TypeSetting",
        text_node: ET.Element,
        paragraph: "Paragraph",
        first_paragraph: bool = False,
        uses_native_positioning: bool = False,
        can_hoist_first_paragraph: bool = False,
    ) -> ET.Element:
        """Add a paragraph to the text node."""
        line_height = paragraph.compute_leading()

        # Positioning based on justification, shape type, and writing direction.
        text_anchor = paragraph.get_text_anchor()
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

        # If using native x, y positioning and this is the first paragraph,
        # and all paragraphs have the same text-anchor value,
        # we can move the positioning to the parent text node instead of tspan.
        if can_hoist_first_paragraph and first_paragraph:
            transform = text_setting.transform
            # Calculate the final absolute position
            final_x = x + transform.tx
            final_y = y + transform.ty

            # Update the parent text node with the final position
            if final_x != 0.0 or text_node.attrib.get("x") is not None:
                svg_utils.set_attribute(text_node, "x", final_x)
            if final_y != 0.0 or text_node.attrib.get("y") is not None:
                svg_utils.set_attribute(text_node, "y", final_y)

            # Also move text-anchor and dominant-baseline to parent if they're set
            if text_anchor is not None:
                svg_utils.set_attribute(text_node, "text-anchor", text_anchor)
            if dominant_baseline is not None:
                svg_utils.set_attribute(text_node, "dominant-baseline", dominant_baseline)

            # Create paragraph node without position attributes (inherited from parent)
            paragraph_node = svg_utils.create_node(
                "tspan",
                parent=text_node,
            )
        else:
            # For non-first paragraphs or when not using native positioning,
            # use the standard approach
            if uses_native_positioning:
                transform = text_setting.transform
                # Only add transform if we're not hoisting the first paragraph
                # (because if we are, the parent already has the transform)
                if not can_hoist_first_paragraph:
                    x += transform.tx
                    y += transform.ty

            # Determine if we should set x, y on the tspan
            # For non-first paragraphs, we typically use dy instead of y
            should_set_x = x != 0.0 or not first_paragraph
            should_set_y = y != 0.0 and first_paragraph

            # Create paragraph node.
            paragraph_node = svg_utils.create_node(
                "tspan",
                parent=text_node,
                text_anchor=text_anchor,
                x=x if should_set_x else None,
                y=y if should_set_y else None,
                dy=line_height if not first_paragraph else None,
                dominant_baseline=dominant_baseline,
            )

        # TODO: There is still a difference with PSD rendering on dominant-baseline.

        # Handle justification.
        if paragraph.justification == Justification.JUSTIFY_ALL:
            logger.info("Justify All is not fully supported in SVG.")
            svg_utils.set_attribute(
                paragraph_node,
                "textLength",
                svg_utils.num2str(text_setting.bounds.width),
            )
            svg_utils.set_attribute(paragraph_node, "lengthAdjust", "spacingAndGlyphs")
        return paragraph_node

    def _add_text_span(
        self, text_setting: "TypeSetting", paragraph_node: ET.Element, span: "Span"
    ) -> ET.Element:
        """Add a text span to the paragraph node."""
        style = span.style
        font_info = text_setting.get_font_info(style.font)

        # Collect font info for later use in rasterization.
        if font_info and font_info.postscript_name not in self.fonts:
            self.fonts[font_info.postscript_name] = font_info

        tspan = svg_utils.create_node(
            "tspan",
            parent=paragraph_node,
            text=span.text.strip("\r"),  # Remove carriage return characters
            font_size=style.font_size,
            font_family=font_info.family_name if font_info else None,
            font_weight="bold"
            if (font_info and font_info.bold) or style.faux_bold
            else None,
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

        if style.tracking != 0:
            # NOTE: Photoshop tracking is in 1/1000 em units.
            svg_utils.set_attribute(
                tspan,
                "letter-spacing",
                svg_utils.num2str(style.tracking / 1000 * style.font_size),
            )

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

    def _merge_singleton_children(self, element: ET.Element) -> None:
        """Merge singleton child nodes into the parent node."""
        for child in list(element):
            self._merge_singleton_children(child)
        if len(element) == 1:
            child = element[0]
            if len(set(element.attrib.keys()) & set(child.attrib.keys())) > 0:
                return  # Conflicting attributes, do not merge

            if child.text:
                element.text = (element.text or "") + child.text
            if child.tail:
                element.tail = (element.tail or "") + child.tail
            for key, value in child.attrib.items():
                if key in element.attrib:
                    logger.debug(
                        f"Overwriting attribute '{key}' from '{element.attrib[key]}' to '{value}'"
                    )
                element.attrib[key] = value
            element.remove(child)

    def _merge_attribute_less_children(self, element: ET.Element) -> None:
        """Merge children without attributes into the parent node."""
        for child in list(element):
            self._merge_attribute_less_children(child)
        for child in list(element):
            if not child.attrib:
                if child.text:
                    element.text = (element.text or "") + child.text
                if child.tail:
                    element.tail = (element.tail or "") + child.tail
                element.remove(child)

    def _merge_common_child_attributes(
        self, element: ET.Element, excludes: set[str]
    ) -> None:
        """Merge common child attributes."""
        for child in list(element):
            self._merge_common_child_attributes(child, excludes)

        # Find attributes that all children have in common with the same value.
        children = list(element)
        if not children:
            return

        # Start with the first child's attributes as candidates
        common_attribs: dict[str, str] = {
            key: value
            for key, value in children[0].attrib.items()
            if key not in excludes
        }

        # Check if remaining children all have the same values
        for child in children[1:]:
            keys_to_remove = []
            for key in common_attribs:
                if key not in child.attrib or child.attrib[key] != common_attribs[key]:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del common_attribs[key]

        # Migrate the common attributes to the parent element.
        for key, value in common_attribs.items():
            element.attrib[key] = value
            for child in element:
                del child.attrib[key]


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
        # TODO: Merge the default paragraph and style sheets.
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

    def get_font_info(self, font_index: int) -> font_utils.FontInfo | None:
        """Get the font family name for the given font index."""
        font_info = self.font_set[font_index]
        postscriptname = font_info.get("Name", None)
        if postscriptname is None:
            logger.warning(f"PostScript name not found for font index {font_index}.")
            return None
        return font_utils.FontInfo.find(postscriptname.value)

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
