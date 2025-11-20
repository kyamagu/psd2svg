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
        ("texts/paragraph-shapetype0-justification0.psd", "start"),
        ("texts/paragraph-shapetype0-justification1.psd", "end"),
        ("texts/paragraph-shapetype0-justification2.psd", "middle"),
    ],
)
def test_text_paragraph_justification(
    psd_file: str, expected_justification: str
) -> None:
    """Test text paragraph justification handling."""
    svg = convert_psd_to_svg(psd_file)
    for node in svg.findall(".//*[@text-anchor]"):
        print(node.attrib)
        assert node.attrib["text-anchor"] == expected_justification


def test_text_span_common_attributes() -> None:
    """Test merging of common attributes in text spans."""
    # The file has multiple paragraphs each with single tspan.
    # We expect the final structure to be: <text> with multiple <tspan>,
    # each with unique font-size.
    svg = convert_psd_to_svg("texts/font-sizes-1.psd")
    # Check that common attributes are merged correctly
    text_node = svg.find(".//text")
    assert text_node is not None
    assert text_node.attrib["text-anchor"] == "start"
    assert text_node.attrib["font-family"] == "Times"
    # Check that individual spans still have their unique attributes
    tspan_nodes = text_node.findall(".//tspan")
    assert len(tspan_nodes) == 4
    font_sizes = tuple(tspan.attrib["font-size"] for tspan in tspan_nodes)
    assert font_sizes == ("16", "18", "21", "24")
