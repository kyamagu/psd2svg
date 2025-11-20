import dataclasses
import logging
import xml.etree.ElementTree as ET
from itertools import groupby
from typing import Any, Iterator

import fontconfig
from psd_tools.api import layers
from psd_tools.psd.descriptor import RawData
from psd_tools.psd.engine_data import DictElement, EngineData
from psd_tools.psd.tagged_blocks import TypeToolObjectSetting

from psd2svg import svg_utils
from psd2svg.core.base import ConverterProtocol
from psd2svg.core import color_utils

logger = logging.getLogger(__name__)


class TypeConverter(ConverterProtocol):
    """Mixin for type layers."""

    def add_type(self, layer: layers.TypeLayer, **attrib: str) -> ET.Element | None:
        """Add a type layer to the svg document."""
        if not self.enable_type:
            return self.add_pixel(layer, **attrib)

        text_setting = TypeSetting(layer._data)
        return self._create_text_node(text_setting)

    def _create_text_node(self, text_setting: "TypeSetting") -> ET.Element:
        """Create SVG text node from type setting."""
        text_node = svg_utils.create_node(
            "text",
            parent=self.current,
            y=text_setting.transform.ty,
        )
        # TODO: Support text wrapping when ShapeType is 1 (Bounding box).
        # TODO: Support transform.
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
        justification = {0: "start", 1: "end", 2: "middle"}[
            int(paragraph.style["Justification"])
        ]
        line_height = (
            max(int(span.style["FontSize"]) for span in paragraph) * 1.2
        )  # Approximate for AutoLeading=True
        # TODO: Support manual leading.
        paragraph_node = svg_utils.create_node(
            "tspan",
            parent=text_node,
            text_anchor=justification,
            x=text_setting.transform.tx,
            dy=line_height if not first_paragraph else None,
        )
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
        return svg_utils.create_node(
            "tspan",
            parent=paragraph_node,
            text=span.text.strip("\r"),  # Remove carriage return characters
            font_size=font_size,
            font_family=font_family,
            fill=fill,
            stroke=stroke,
            baseline_shift=baseline_shift,
        )

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
