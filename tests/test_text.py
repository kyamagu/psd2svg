import pytest
import xml.etree.ElementTree as ET
from psd_tools import PSDImage

from psd2svg.core.converter import Converter

from .conftest import get_fixture, requires_noto_sans_jp

try:
    import fontconfig

    _TIMES_FONT_AVAILABLE = bool(
        fontconfig.query(where=":postscriptname=Times-Roman", select=("family",))
    )
    _ARIAL_FONT_AVAILABLE = bool(
        fontconfig.query(where=":postscriptname=ArialMT", select=("family",))
    )
except Exception:
    _TIMES_FONT_AVAILABLE = False
    _ARIAL_FONT_AVAILABLE = False


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


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_bold() -> None:
    """Test bold font weight handling.

    Bold fonts should have font-weight="700" (CSS numeric value).
    This works better with variable fonts than the keyword "bold".
    """
    svg = convert_psd_to_svg("texts/style-bold.psd")
    # Find all tspans with font-weight
    tspans = svg.findall(".//tspan[@font-weight]")
    assert len(tspans) > 0, "Should have at least one tspan with font-weight"

    # Check that we have a bold tspan (weight 700)
    font_weights = [t.attrib.get("font-weight") for t in tspans]
    assert "700" in font_weights, (
        f"Expected to find font-weight='700' (bold), got: {font_weights}"
    )


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_italic() -> None:
    """Test italic font style handling."""
    svg = convert_psd_to_svg("texts/style-italic.psd")
    tspan = svg.find(".//tspan[@font-style]")
    assert tspan is not None
    assert tspan.attrib.get("font-style") == "italic"


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_faux_bold() -> None:
    """Test faux bold handling.

    Faux bold (synthetic bold) should set font-weight="700".
    This ensures proper rendering even with variable fonts.
    """
    svg = convert_psd_to_svg("texts/style-faux-bold.psd")
    # Find all tspans with font-weight
    tspans = svg.findall(".//tspan[@font-weight]")
    assert len(tspans) > 0, "Should have at least one tspan with font-weight"

    # Check that we have a bold tspan (weight 700 for faux bold)
    font_weights = [t.attrib.get("font-weight") for t in tspans]
    assert "700" in font_weights, (
        f"Expected to find font-weight='700' (faux bold), got: {font_weights}"
    )


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_faux_italic() -> None:
    """Test faux italic handling."""
    svg = convert_psd_to_svg("texts/style-faux-italic.psd")
    tspan = svg.find(".//tspan[@font-style]")
    assert tspan is not None
    assert tspan.attrib.get("font-style") == "italic"


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_underline() -> None:
    """Test underline text decoration handling."""
    svg = convert_psd_to_svg("texts/style-underline.psd")
    tspan = svg.find(".//tspan[@text-decoration]")
    assert tspan is not None
    assert "underline" in tspan.attrib.get("text-decoration", "")


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_strikethrough() -> None:
    """Test strikethrough text decoration handling."""
    svg = convert_psd_to_svg("texts/style-strikethrough.psd")
    tspan = svg.find(".//tspan[@text-decoration]")
    assert tspan is not None
    assert "line-through" in tspan.attrib.get("text-decoration", "")


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_all_caps() -> None:
    """Test all-caps text transform handling."""
    svg = convert_psd_to_svg("texts/style-all-caps.psd")
    tspan = svg.find(".//tspan")
    assert tspan is not None
    style = tspan.attrib.get("style", "")
    assert "text-transform: uppercase" in style or "text-transform:uppercase" in style


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_small_caps() -> None:
    """Test small-caps font variant handling."""
    svg = convert_psd_to_svg("texts/style-small-caps.psd")
    tspan = svg.find(".//tspan[@font-variant]")
    assert tspan is not None
    assert tspan.attrib.get("font-variant") == "small-caps"


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
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


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
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


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_baseline_shift() -> None:
    """Test baseline shift handling."""
    svg = convert_psd_to_svg("texts/style-baseline-shift.psd")
    # baseline-shift can be on text or tspan elements
    element = svg.find(".//*[@baseline-shift]")
    assert element is not None
    # Should have non-zero baseline shift
    baseline_shift = float(element.attrib.get("baseline-shift", "0"))
    assert baseline_shift != 0


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_tracking() -> None:
    """Test tracking (letter-spacing) handling."""
    svg = convert_psd_to_svg("texts/style-tracking.psd")
    tspan = svg.find(".//tspan[@letter-spacing]")
    assert tspan is not None
    # Should have non-zero letter spacing
    letter_spacing = float(tspan.attrib.get("letter-spacing", "0"))
    assert letter_spacing != 0


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
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


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_horizontal_scale() -> None:
    """Test horizontal scale transform handling."""
    svg = convert_psd_to_svg("texts/style-horizontally-scale-50.psd")
    # Check for transform on tspan or text element (optimization may move it to text)
    element = svg.find(".//tspan[@transform]")
    if element is None:
        element = svg.find(".//text[@transform]")
    assert element is not None
    transform = element.attrib.get("transform", "")
    # Should contain scale transformation
    assert "scale" in transform
    # Should have horizontal scale of 0.5 (50%)
    assert "0.5" in transform or ".5" in transform


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_style_vertical_scale() -> None:
    """Test vertical scale transform handling."""
    svg = convert_psd_to_svg("texts/style-vertically-scale-50.psd")
    # Check for transform on tspan or text element (optimization may move it to text)
    element = svg.find(".//tspan[@transform]")
    if element is None:
        element = svg.find(".//text[@transform]")
    assert element is not None
    transform = element.attrib.get("transform", "")
    # Should contain scale transformation
    assert "scale" in transform
    # Should have vertical scale of 0.5 (50%)
    assert "0.5" in transform or ".5" in transform


def test_text_native_positioning_point_type() -> None:
    """Test that point-type text uses native x, y attributes instead of transform."""
    svg = convert_psd_to_svg("texts/paragraph-shapetype0-justification0.psd")
    text_node = svg.find(".//text")
    assert text_node is not None
    # Should use native x, y attributes for translation-only transforms
    assert text_node.attrib.get("x") is not None
    assert text_node.attrib.get("y") is not None
    # Should not have a transform attribute (translation-only)
    assert text_node.attrib.get("transform") is None


def test_text_native_positioning_bounding_box_left() -> None:
    """Test that bounding box with left alignment uses native x, y on text node."""
    svg = convert_psd_to_svg("texts/paragraph-shapetype1-justification0.psd")
    text_node = svg.find(".//text")
    assert text_node is not None
    # Should use native x, y attributes
    assert text_node.attrib.get("x") is not None
    assert text_node.attrib.get("y") is not None
    # Should not have a transform attribute
    assert text_node.attrib.get("transform") is None


def test_text_native_positioning_bounding_box_right() -> None:
    """Test that bounding box with right alignment correctly combines transform and bounds on text node."""
    svg = convert_psd_to_svg("texts/paragraph-shapetype1-justification1.psd")
    text_node = svg.find(".//text")
    assert text_node is not None
    # Should use native x, y attributes on text node with combined position
    text_x = float(text_node.attrib.get("x", "0"))
    text_y = float(text_node.attrib.get("y", "0"))
    assert text_x != 0
    assert text_y != 0
    # Should not have a transform attribute on text
    assert text_node.attrib.get("transform") is None
    # Should have text-anchor for right alignment
    assert text_node.attrib.get("text-anchor") == "end"
    # x should be greater than just the transform tx (includes bounds.right)
    # For this test file, transform.tx is about 23, but with bounds it should be ~217
    assert text_x > 100


def test_text_native_positioning_bounding_box_center() -> None:
    """Test that bounding box with center alignment correctly combines transform and bounds on text node."""
    svg = convert_psd_to_svg("texts/paragraph-shapetype1-justification2.psd")
    text_node = svg.find(".//text")
    assert text_node is not None
    # Should use native x, y attributes on text node with combined position
    text_x = float(text_node.attrib.get("x", "0"))
    text_y = float(text_node.attrib.get("y", "0"))
    assert text_x != 0
    assert text_y != 0
    # Should not have a transform attribute on text
    assert text_node.attrib.get("transform") is None
    # Should have text-anchor for center alignment
    assert text_node.attrib.get("text-anchor") == "middle"
    # x should be greater than just the transform tx (includes midpoint)
    # For this test file, transform.tx is about 23, but with bounds midpoint it should be ~120
    assert text_x > 50


@pytest.mark.skipif(not _ARIAL_FONT_AVAILABLE, reason="Arial font not available")
def test_text_multiple_paragraphs_different_alignments() -> None:
    """Test that multiple paragraphs with different text anchors are handled correctly.

    When paragraphs have different text-anchor values (e.g., left, center, right),
    the native positioning optimization should NOT hoist the first paragraph's
    attributes to the parent text node. Instead, each paragraph should have its
    own tspan with appropriate positioning and text-anchor.
    """
    svg = convert_psd_to_svg("texts/paragraph-shapetype1-multiple.psd")
    text_node = svg.find(".//text")
    assert text_node is not None

    # The parent text node should use native x, y positioning (translation only)
    assert text_node.attrib.get("x") is not None
    assert text_node.attrib.get("y") is not None
    assert text_node.attrib.get("transform") is None

    # Get all tspan elements (one per paragraph)
    tspans = text_node.findall("tspan")
    assert len(tspans) == 3  # Three paragraphs

    # First paragraph: RIGHT alignment (text-anchor="end")
    assert tspans[0].attrib.get("text-anchor") == "end"
    assert tspans[0].attrib.get("x") is not None
    assert tspans[0].attrib.get("y") is not None  # First paragraph has y
    assert tspans[0].attrib.get("dy") is None  # First paragraph doesn't have dy

    # Second paragraph: CENTER alignment (text-anchor="middle")
    assert tspans[1].attrib.get("text-anchor") == "middle"
    assert tspans[1].attrib.get("x") is not None
    assert tspans[1].attrib.get("y") is None  # Non-first paragraphs don't have y
    assert tspans[1].attrib.get("dy") is not None  # Non-first paragraphs have dy

    # Third paragraph: LEFT alignment (text-anchor=None or not set)
    third_text_anchor = tspans[2].attrib.get("text-anchor")
    assert third_text_anchor is None or third_text_anchor == "start"
    assert tspans[2].attrib.get("x") is not None
    assert tspans[2].attrib.get("y") is None  # Non-first paragraphs don't have y
    assert tspans[2].attrib.get("dy") is not None  # Non-first paragraphs have dy

    # Verify that each paragraph has the correct x position
    # (based on bounds and alignment)
    tspan_x_values = [float(t.attrib.get("x", "0")) for t in tspans]
    # Right-aligned should have the largest x
    # Center should be in the middle
    # Left should have the smallest x
    assert tspan_x_values[0] > tspan_x_values[1] > tspan_x_values[2]


def test_text_bounding_box_dominant_baseline() -> None:
    """Test that bounding box text (ShapeType=1) uses dominant-baseline="hanging".

    Bounding box text should set dominant-baseline="hanging" which aligns text
    to the hanging baseline (top of capital letters), providing better visual
    alignment with Photoshop's rendering compared to "text-before-edge".
    """
    # Test with a bounding box left-aligned text
    svg = convert_psd_to_svg("texts/paragraph-shapetype1-justification0.psd")
    text_node = svg.find(".//text")
    assert text_node is not None

    # Should have dominant-baseline="hanging" for bounding box text
    assert text_node.attrib.get("dominant-baseline") == "hanging"

    # Test with multiple paragraphs
    svg = convert_psd_to_svg("texts/paragraph-shapetype1-multiple.psd")
    text_node = svg.find(".//text")
    assert text_node is not None

    # Should also have dominant-baseline="hanging"
    assert text_node.attrib.get("dominant-baseline") == "hanging"


def test_text_point_type_no_dominant_baseline() -> None:
    """Test that point text (ShapeType=0) does NOT set dominant-baseline.

    Point text should not have dominant-baseline attribute since it doesn't
    use bounding box positioning.
    """
    # Test with a point-type text
    svg = convert_psd_to_svg("texts/paragraph-shapetype0-justification0.psd")
    text_node = svg.find(".//text")
    assert text_node is not None

    # Should NOT have dominant-baseline for point text
    assert text_node.attrib.get("dominant-baseline") is None


@requires_noto_sans_jp
def test_text_japanese_notosans_jp() -> None:
    """Test Japanese text rendering with Noto Sans JP font.

    This test verifies that:
    1. Japanese text content is preserved in the SVG
    2. The font-family is set to Noto Sans JP (not a fallback font)
    3. Text elements are properly created
    4. The text is rendered (not rasterized as an image)

    Note: The PSD file specifies "NotoSansJP-Regular" as the PostScript name,
    which should resolve to "Noto Sans JP" family name via fontconfig.
    """
    svg = convert_psd_to_svg("texts/fonts-notosans-jp.psd")

    # Find all text elements
    text_nodes = svg.findall(".//text")
    assert len(text_nodes) > 0, "Should have at least one text element"

    # Check the first text element
    text_node = text_nodes[0]

    # Verify Japanese text content is present (美しい日本語 = Beautiful Japanese)
    text_content = "".join(text_node.itertext())
    assert "美しい日本語" in text_content, f"Japanese text not found. Got: {text_content}"

    # Verify font-family is set to Noto Sans JP (not a fallback)
    font_family = text_node.attrib.get("font-family")
    assert font_family is not None, "font-family should be set"
    assert font_family == "Noto Sans JP", (
        f"Expected font-family to be exactly 'Noto Sans JP', got: '{font_family}'. "
        "If you see a different Noto font (like 'Noto Sans Yi'), it means "
        "'Noto Sans JP' is not properly installed and fontconfig fell back to another font."
    )
