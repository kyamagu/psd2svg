import pytest
from psd_tools import PSDImage

from psd2svg.core.converter import Converter

from .conftest import get_fixture


@pytest.mark.parametrize(
    "psd_file, expected_justification",
    [
        ("texts/paragraph-shapetype0-justification0.psd", "start"),
        ("texts/paragraph-shapetype0-justification1.psd", "end"),
        ("texts/paragraph-shapetype0-justification2.psd", "middle"),
    ],
)
def test_text_paragraph_justification(psd_file: str, expected_justification: str) -> None:
    """Test text paragraph justification handling."""
    psdimage = PSDImage.open(get_fixture(psd_file))
    converter = Converter(psdimage)
    converter.build()
    for node in converter.svg.findall(".//*[@text-anchor]"):
        print(node.attrib)
        assert node.attrib["text-anchor"] == expected_justification