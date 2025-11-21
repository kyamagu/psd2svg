import pytest
import xml.etree.ElementTree as ET
from psd_tools import PSDImage

from psd2svg.core.converter import Converter

from .conftest import get_fixture

try:
    import fontconfig

    _TIMES_FONT_AVAILABLE = bool(
        fontconfig.query(where=":postscriptname=Times-Roman", select=("family",))
    )
except Exception:
    _TIMES_FONT_AVAILABLE = False


def convert_psd_to_svg(psd_file: str) -> ET.Element:
    """Convert a PSD file to SVG and return the SVG as a string."""
    psdimage = PSDImage.open(get_fixture(psd_file))
    converter = Converter(psdimage)
    converter.build()
    return converter.svg


@pytest.mark.parametrize(
    "psd_file, expected_justification",
    [
        # Horizontal text cases
        ("texts/paragraph-shapetype0-justification0.psd", None),
        ("texts/paragraph-shapetype0-justification1.psd", "end"),
        ("texts/paragraph-shapetype0-justification2.psd", "middle"),
        ("texts/paragraph-shapetype1-justification0.psd", None),
        ("texts/paragraph-shapetype1-justification1.psd", "end"),
        ("texts/paragraph-shapetype1-justification2.psd", "middle"),
        ("texts/paragraph-shapetype1-justification3.psd", None),
        ("texts/paragraph-shapetype1-justification4.psd", "end"),
        ("texts/paragraph-shapetype1-justification5.psd", "middle"),
        # Vertical text cases
        (
            "texts/shapetype0-writingdirection2-baselinedirection2-justification0.psd",
            None,
        ),
        (
            "texts/shapetype0-writingdirection2-baselinedirection2-justification1.psd",
            "end",
        ),
        (
            "texts/shapetype0-writingdirection2-baselinedirection2-justification2.psd",
            "middle",
        ),
        (
            "texts/shapetype1-writingdirection2-baselinedirection2-justification0.psd",
            None,
        ),
        (
            "texts/shapetype1-writingdirection2-baselinedirection2-justification1.psd",
            "end",
        ),
        (
            "texts/shapetype1-writingdirection2-baselinedirection2-justification2.psd",
            "middle",
        ),
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
    # Only check font-family if Times font is available on the system
    if _TIMES_FONT_AVAILABLE:
        assert text_node.attrib.get("font-family") == "Times"
    # Check that individual spans still have their unique attributes
    tspan_nodes = text_node.findall(".//tspan")
    assert len(tspan_nodes) == 4
    # Check that font sizes are present and different (actual values may vary slightly)
    font_sizes = [float(tspan.attrib["font-size"]) for tspan in tspan_nodes]
    assert len(set(font_sizes)) == 4  # All different sizes
    assert all(size > 0 for size in font_sizes)  # All positive


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


def test_text_writing_direction() -> None:
    """Test text writing direction handling."""

    # Vertical Right to Left, characters upright
    # NOTE: Only Chromium-based browsers support 'text-orientation: upright' for SVG.
    svg = convert_psd_to_svg(
        "texts/shapetype0-writingdirection2-baselinedirection1-justification0.psd"
    )
    text_node = svg.find(".//text")
    assert text_node is not None
    assert text_node.attrib.get("writing-mode") == "vertical-rl"
    assert text_node.attrib.get("style") == "text-orientation: upright"

    # Vertical Right to Left, baseline direction
    svg = convert_psd_to_svg(
        "texts/shapetype0-writingdirection2-baselinedirection2-justification0.psd"
    )
    text_node = svg.find(".//text")
    assert text_node is not None
    assert text_node.attrib.get("writing-mode") == "vertical-rl"
    assert text_node.attrib.get("style") is None


def test_text_style_bold() -> None:
    """Test bold font weight handling."""
    svg = convert_psd_to_svg("texts/style-bold.psd")
    tspan = svg.find(".//tspan[@font-weight]")
    assert tspan is not None
    assert tspan.attrib.get("font-weight") == "bold"


def test_text_style_italic() -> None:
    """Test italic font style handling."""
    svg = convert_psd_to_svg("texts/style-italic.psd")
    tspan = svg.find(".//tspan[@font-style]")
    assert tspan is not None
    assert tspan.attrib.get("font-style") == "italic"


def test_text_style_faux_bold() -> None:
    """Test faux bold handling."""
    svg = convert_psd_to_svg("texts/style-faux-bold.psd")
    tspan = svg.find(".//tspan[@font-weight]")
    assert tspan is not None
    assert tspan.attrib.get("font-weight") == "bold"


def test_text_style_faux_italic() -> None:
    """Test faux italic handling."""
    svg = convert_psd_to_svg("texts/style-faux-italic.psd")
    tspan = svg.find(".//tspan[@font-style]")
    assert tspan is not None
    assert tspan.attrib.get("font-style") == "italic"


def test_text_style_underline() -> None:
    """Test underline text decoration handling."""
    svg = convert_psd_to_svg("texts/style-underline.psd")
    tspan = svg.find(".//tspan[@text-decoration]")
    assert tspan is not None
    assert "underline" in tspan.attrib.get("text-decoration", "")


def test_text_style_strikethrough() -> None:
    """Test strikethrough text decoration handling."""
    svg = convert_psd_to_svg("texts/style-strikethrough.psd")
    tspan = svg.find(".//tspan[@text-decoration]")
    assert tspan is not None
    assert "line-through" in tspan.attrib.get("text-decoration", "")


def test_text_style_all_caps() -> None:
    """Test all-caps text transform handling."""
    svg = convert_psd_to_svg("texts/style-all-caps.psd")
    tspan = svg.find(".//tspan")
    assert tspan is not None
    style = tspan.attrib.get("style", "")
    assert "text-transform: uppercase" in style or "text-transform:uppercase" in style


def test_text_style_small_caps() -> None:
    """Test small-caps font variant handling."""
    svg = convert_psd_to_svg("texts/style-small-caps.psd")
    tspan = svg.find(".//tspan[@font-variant]")
    assert tspan is not None
    assert tspan.attrib.get("font-variant") == "small-caps"


def test_text_style_superscript() -> None:
    """Test superscript baseline shift and font size handling."""
    svg = convert_psd_to_svg("texts/style-superscript.psd")
    tspan = svg.find(".//tspan[@baseline-shift]")
    assert tspan is not None
    # Should have positive baseline shift
    baseline_shift = float(tspan.attrib.get("baseline-shift", "0"))
    assert baseline_shift > 0
    # Should have reduced font size
    assert tspan.attrib.get("font-size") is not None


def test_text_style_subscript() -> None:
    """Test subscript baseline shift and font size handling."""
    svg = convert_psd_to_svg("texts/style-subscript.psd")
    tspan = svg.find(".//tspan[@baseline-shift]")
    assert tspan is not None
    # Should have negative baseline shift
    baseline_shift = float(tspan.attrib.get("baseline-shift", "0"))
    assert baseline_shift < 0
    # Should have reduced font size
    assert tspan.attrib.get("font-size") is not None


def test_text_style_baseline_shift() -> None:
    """Test baseline shift handling."""
    svg = convert_psd_to_svg("texts/style-baseline-shift.psd")
    # baseline-shift can be on text or tspan elements
    element = svg.find(".//*[@baseline-shift]")
    assert element is not None
    # Should have non-zero baseline shift
    baseline_shift = float(element.attrib.get("baseline-shift", "0"))
    assert baseline_shift != 0


def test_text_style_tracking() -> None:
    """Test tracking (letter-spacing) handling."""
    svg = convert_psd_to_svg("texts/style-tracking.psd")
    tspan = svg.find(".//tspan[@letter-spacing]")
    assert tspan is not None
    # Should have non-zero letter spacing
    letter_spacing = float(tspan.attrib.get("letter-spacing", "0"))
    assert letter_spacing != 0


def test_text_style_leading() -> None:
    """Test leading (line height) handling."""
    svg = convert_psd_to_svg("texts/style-leading.psd")
    # Leading affects dy attribute on tspan elements for subsequent paragraphs
    tspans = svg.findall(".//tspan[@dy]")
    # Should have at least one tspan with dy attribute (second paragraph onwards)
    assert len(tspans) > 0
    # dy should be non-zero
    dy = float(tspans[0].attrib.get("dy", "0"))
    assert dy != 0


def test_text_style_horizontal_scale() -> None:
    """Test horizontal scale transform handling."""
    svg = convert_psd_to_svg("texts/style-horizontally-scale-50.psd")
    tspan = svg.find(".//tspan[@transform]")
    assert tspan is not None
    transform = tspan.attrib.get("transform", "")
    # Should contain scale transformation
    assert "scale" in transform
    # Should have horizontal scale of 0.5 (50%)
    assert "0.5" in transform or ".5" in transform


def test_text_style_vertical_scale() -> None:
    """Test vertical scale transform handling."""
    svg = convert_psd_to_svg("texts/style-vertically-scale-50.psd")
    tspan = svg.find(".//tspan[@transform]")
    assert tspan is not None
    transform = tspan.attrib.get("transform", "")
    # Should contain scale transformation
    assert "scale" in transform
    # Should have vertical scale of 0.5 (50%)
    assert "0.5" in transform or ".5" in transform
