import pytest
import xml.etree.ElementTree as ET
from psd_tools import PSDImage

from psd2svg.core.converter import Converter

from .conftest import get_fixture


def convert_psd_to_svg(psd_file: str) -> ET.Element:
    """Convert a PSD file to SVG and return the SVG as a string."""
    psdimage = PSDImage.open(get_fixture(psd_file))
    converter = Converter(psdimage)
    converter.build()
    return converter.svg


@pytest.mark.parametrize(
    "psd_file, expected_justification",
    [
        ("texts/paragraph-shapetype0-justification0.psd", None),
        ("texts/paragraph-shapetype0-justification1.psd", "end"),
        ("texts/paragraph-shapetype0-justification2.psd", "middle"),
        ("texts/paragraph-shapetype1-justification0.psd", None),
        ("texts/paragraph-shapetype1-justification1.psd", "end"),
        ("texts/paragraph-shapetype1-justification2.psd", "middle"),
        ("texts/paragraph-shapetype1-justification3.psd", None),
        ("texts/paragraph-shapetype1-justification4.psd", "end"),
        ("texts/paragraph-shapetype1-justification5.psd", "middle"),
    ],
)
def test_text_paragraph_justification(
    psd_file: str, expected_justification: str | None
) -> None:
    """Test text paragraph justification handling."""
    svg = convert_psd_to_svg(psd_file)
    for node in svg.findall(".//*[@text-anchor]"):
        assert node.attrib.get("text-anchor") == expected_justification


def test_text_paragraph_justification_justify() -> None:
    """Test text paragraph justification handling for 'justify' case."""
    svg = convert_psd_to_svg("texts/paragraph-shapetype1-justification6.psd")
    node = svg.find(".//*[@text-anchor]")
    assert node is None
    node = svg.find(".//*[@textLength]")
    assert node is not None
    assert node.attrib.get("textLength") is not None
    assert node.attrib.get("lengthAdjust") == "spacingAndGlyphs"


def test_text_span_common_attributes() -> None:
    """Test merging of common attributes in text spans."""
    # The file has multiple paragraphs each with single tspan.
    # We expect the final structure to be: <text> with multiple <tspan>,
    # each with unique font-size.
    svg = convert_psd_to_svg("texts/font-sizes-1.psd")
    # Check that common attributes are merged correctly
    text_node = svg.find(".//text")
    assert text_node is not None
    assert text_node.attrib.get("text-anchor") is None
    assert text_node.attrib.get("font-family") == "Times"
    # Check that individual spans still have their unique attributes
    tspan_nodes = text_node.findall(".//tspan")
    assert len(tspan_nodes) == 4
    font_sizes = tuple(tspan.attrib["font-size"] for tspan in tspan_nodes)
    assert font_sizes == ("16", "18", "21", "24")


def test_text_paragraph_positions() -> None:
    """Test text paragraph positions handling."""
    svg = convert_psd_to_svg("texts/font-sizes-1.psd")
    text_node = svg.find(".//text")
    assert text_node is not None
    tspan_nodes = text_node.findall(".//tspan")
    assert len(tspan_nodes) == 4
    # First tspan should not have x or dy set
    assert tspan_nodes[0].attrib.get("x") is None
    assert tspan_nodes[0].attrib.get("dy") is None
    # Second to fourth tspans should have x="0" and dy set
    for i in range(1, 4):
        assert tspan_nodes[i].attrib.get("x") == "0"
        assert tspan_nodes[i].attrib.get("dy") is not None
