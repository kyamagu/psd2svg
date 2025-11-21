import dataclasses
import logging
import xml.etree.ElementTree as ET
from enum import IntEnum
from itertools import groupby
from typing import Any, Iterator

import fontconfig
from psd_tools.api import layers
from psd_tools.psd.descriptor import RawData
from psd_tools.psd.engine_data import DictElement, EngineData
from psd_tools.psd.tagged_blocks import TypeToolObjectSetting
from psd_tools.terminology import Key

from psd2svg import svg_utils
from psd2svg.core import color_utils
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


class TypeConverter(ConverterProtocol):
    """Mixin for type layers."""

    def add_type(self, layer: layers.TypeLayer, **attrib: str) -> ET.Element | None:
        """Add a type layer to the svg document."""
        if not self.enable_text:
            return self.add_pixel(layer, **attrib)

        text_setting = TypeSetting(layer._data)
        return self._create_text_node(text_setting)

    def _create_text_node(self, text_setting: "TypeSetting") -> ET.Element:
        """Create SVG text node from type setting."""
        text_node = svg_utils.create_node(
            "text",
            parent=self.current,
            transform=text_setting.transform.to_svg_matrix(),
        )
        if text_setting.writing_direction == WritingDirection.VERTICAL_RL:
            svg_utils.set_attribute(text_node, "writing-mode", "vertical-rl")
        # TODO: Support text wrapping when ShapeType is 1 (Bounding box).
        # TODO: Support adjustments.
        for i, paragraph in enumerate(text_setting):
            paragraph_node = self._add_paragraph(
                text_setting, text_node, paragraph, first_paragraph=(i == 0)
            )
            for span in paragraph:
                self._add_text_span(text_setting, paragraph_node, span)

        self._merge_common_child_attributes(text_node, excludes={"x", "y", "dx", "dy"})
        self._merge_singleton_children(text_node)
        self._merge_attribute_less_children(text_node)
        return text_node

    def _add_paragraph(
        self,
        text_setting: "TypeSetting",
        text_node: ET.Element,
        paragraph: "Paragraph",
        first_paragraph: bool = False,
    ) -> ET.Element:
        """Add a paragraph to the text node."""

        # Approximate line height
        line_height = (
            max(int(span.style["FontSize"]) for span in paragraph) * 1.2
        )  # Approximate for AutoLeading=True
        # TODO: Support manual leading.

        # Positioning based on justification, shape type, and writing direction.
        text_anchor = paragraph.get_text_anchor()
        x = 0.0
        y = 0.0
        dominant_baseline = None
        if text_setting.shape_type == ShapeType.BOUNDING_BOX:
            dominant_baseline = "text-before-edge"
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

        # Create paragraph node.
        paragraph_node = svg_utils.create_node(
            "tspan",
            parent=text_node,
            text_anchor=text_anchor,
            x=None if x == 0.0 and first_paragraph else x,
            y=None if y == 0.0 and first_paragraph else y,
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
        font_family = find_font_family(
            postscriptname=text_setting.font_set[span.style["Font"]]["Name"].value
        )
        font_size = int(span.style["FontSize"])
        fill = (
            get_paint_content(span.style["FillColor"])
            if span.style["FillFlag"]
            else None
        )
        stroke = (
            get_paint_content(span.style["StrokeColor"])
            if span.style["StrokeFlag"]
            else None
        )
        baseline_shift = None
        if span.style.get("BaselineShift") is not None:
            shift_value = span.style["BaselineShift"].value
            if shift_value != 0:
                baseline_shift = shift_value
        tspan = svg_utils.create_node(
            "tspan",
            parent=paragraph_node,
            text=span.text.strip("\r"),  # Remove carriage return characters
            font_size=font_size,
            font_family=font_family,
            fill=fill,
            stroke=stroke,
            baseline_shift=baseline_shift,
        )
        if span.style.get("BaselineDirection") == 1:
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
            if child.text:
                element.text = (element.text or "") + child.text
            if child.tail:
                element.tail = (element.tail or "") + child.tail
            for key, value in child.attrib.items():
                if key in element.attrib:
                    # This is expected because text is always inserted into leaf tspans,
                    # and we're now hoisting child attributes to the parent.
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
        common_attribs: dict[str, str | None] = {}
        for child in element:
            for key, value in child.attrib.items():
                if key in excludes:
                    continue
                if key not in common_attribs:
                    common_attribs[key] = value
                elif common_attribs[key] != value:
                    common_attribs[key] = None
        for key, value in common_attribs.items():  # type: ignore
            if value is not None:
                element.attrib[key] = value
                for child in element:
                    if key in child.attrib:
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
        return Justification(self.style.get("Justification", 0))

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


def find_font_family(postscriptname: str) -> str | None:
    """Find the font family name for the given span index."""
    results = fontconfig.query(
        where=f":postscriptname={postscriptname}", select=("family",)
    )
    if not results:
        logger.warning(
            f"Font file for '{postscriptname}' not found. "
            "Make sure the font is installed on your system."
        )
        return None
    return results[0]["family"][0]  # type: ignore


def get_paint_content(paint: dict) -> str | None:
    """Get the paint content from the style sheet."""
    if paint is None:
        logger.info("Paint content not found in style sheet.")
        return None
    if paint["Type"].value != 1:
        # TODO: Check other paint types like gradients and patterns if any.
        logger.info(
            f"Unsupported Paint type: {paint['Type'].value}. Only Solid color is supported."
        )
        return None

    values = paint["Values"]
    # Assuming fill_color is in ARGB format with values between 0 and 1.
    r = int(values[1] * 255)
    g = int(values[2] * 255)
    b = int(values[3] * 255)
    a = values[0]
    if a == 0:
        return "none"
    elif ((r, g, b) == (0, 0, 0)) and (a == 1):
        return None  # Default black color in SVG.
    return color_utils.rgba2hex((r, g, b), alpha=a)
