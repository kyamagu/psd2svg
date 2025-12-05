import pytest
import xml.etree.ElementTree as ET
from psd_tools import PSDImage

from psd2svg import SVGDocument
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
    # Check that individual spans still have their unique attributes
    tspan_nodes = text_node.findall(".//tspan")
    assert len(tspan_nodes) == 4
    # Check that font sizes are present and different (actual values may vary slightly)
    font_sizes = [float(tspan.attrib["font-size"]) for tspan in tspan_nodes]
    assert len(set(font_sizes)) == 4  # All different sizes
    assert all(size > 0 for size in font_sizes)  # All positive


def test_text_paragraph_positions() -> None:
    """Test text paragraph positions handling with consistent structure."""
    svg = convert_psd_to_svg("texts/font-sizes-1.psd")
    text_node = svg.find(".//text")
    assert text_node is not None

    # Parent text node should NOT have x and y (all tspans have their own positions)
    assert text_node.attrib.get("x") is None
    assert text_node.attrib.get("y") is None

    tspan_nodes = text_node.findall(".//tspan")
    assert len(tspan_nodes) == 4

    # All tspans should have x attribute
    # First tspan should have x and y
    assert tspan_nodes[0].attrib.get("x") is not None
    assert tspan_nodes[0].attrib.get("y") is not None
    assert tspan_nodes[0].attrib.get("dy") is None

    # Subsequent tspans should have x and dy (no y)
    # All should have same x value (to reset to left margin)
    first_x = tspan_nodes[0].attrib.get("x")
    for i in range(1, 4):
        assert tspan_nodes[i].attrib.get("x") == first_x, (
            f"tspan {i} should have x='{first_x}' to reset to left margin"
        )
        assert tspan_nodes[i].attrib.get("y") is None, (
            f"tspan {i} should not have y (uses dy instead)"
        )
        assert tspan_nodes[i].attrib.get("dy") is not None, (
            f"tspan {i} should have dy for line spacing"
        )


def test_text_paragraph_native_positioning_no_x_override() -> None:
    """Test that all paragraphs have consistent x positioning.

    Regression test for alignment issues. The current implementation gives all
    paragraphs consistent structure: each tspan has explicit x positioning.

    The correct behavior is for all tspans to:
    - Have x attribute set to the same value (to maintain left margin alignment)
    - First tspan has x and y (initial position)
    - Subsequent tspans have x and dy (reset horizontal, offset vertical)
    """
    svg = convert_psd_to_svg("texts/font-sizes-1.psd")
    text_node = svg.find(".//text")
    assert text_node is not None

    # Verify we're using native positioning (no transform on parent)
    assert text_node.attrib.get("transform") is None, (
        "Parent text node should not have transform (using native positioning)"
    )

    tspan_nodes = text_node.findall(".//tspan")
    assert len(tspan_nodes) >= 2, "Need at least 2 paragraphs to test"

    # First paragraph tspan should have x and y
    first_x = tspan_nodes[0].attrib.get("x")
    first_y = tspan_nodes[0].attrib.get("y")
    assert first_x is not None, "First tspan should have x attribute"
    assert first_y is not None, "First tspan should have y attribute"
    assert tspan_nodes[0].attrib.get("dy") is None, "First tspan should not have dy"

    # Parse the x value to verify it's non-zero (not at origin)
    first_x_value = float(first_x)
    assert first_x_value != 0.0, "First tspan x should be non-zero for this test"

    # All subsequent paragraph tspans should:
    # 1. Have x set to same value as first (to reset horizontal position)
    # 2. Have dy attribute for vertical offset
    # 3. NOT have y attribute (using dy instead)
    for i in range(1, len(tspan_nodes)):
        tspan = tspan_nodes[i]

        # Critical: x should be set consistently across all tspans
        x_attr = tspan.attrib.get("x")
        assert x_attr == first_x, (
            f"Paragraph {i + 1} tspan should have x='{first_x}', but has x='{x_attr}'. "
            f"Without consistent x, text would continue from end of previous line."
        )

        # Should have dy for line spacing
        dy_attr = tspan.attrib.get("dy")
        assert dy_attr is not None, (
            f"Paragraph {i + 1} tspan should have dy attribute for vertical offset"
        )

        # Should not have y (using dy instead for relative positioning)
        y_attr = tspan.attrib.get("y")
        assert y_attr is None, (
            f"Paragraph {i + 1} tspan should not have y attribute (should use dy instead)"
        )


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


def test_text_style_italic() -> None:
    """Test italic font style handling."""
    svg = convert_psd_to_svg("texts/style-italic.psd")
    tspan = svg.find(".//tspan[@font-style]")
    assert tspan is not None
    assert tspan.attrib.get("font-style") == "italic"


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
    # After merge_common_child_attributes, style may be on parent text node or tspans
    text = svg.find(".//text")
    assert text is not None

    # Check text node and all tspans for the style
    text_style = text.attrib.get("style", "")
    tspans = svg.findall(".//tspan")
    tspan_styles = " ".join(t.attrib.get("style", "") for t in tspans)
    combined_style = text_style + " " + tspan_styles
    assert (
        "text-transform: uppercase" in combined_style
        or "text-transform:uppercase" in combined_style
    )


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


def test_text_letter_spacing_offset() -> None:
    """Test text_letter_spacing_offset parameter."""
    # Test with no offset (default behavior)
    psdimage = PSDImage.open(get_fixture("texts/style-tracking.psd"))
    doc_no_offset = SVGDocument.from_psd(psdimage, text_letter_spacing_offset=0.0)
    tspan_no_offset = doc_no_offset.svg.find(".//tspan[@letter-spacing]")
    assert tspan_no_offset is not None
    letter_spacing_no_offset = float(tspan_no_offset.attrib.get("letter-spacing", "0"))

    # Test with positive offset
    doc_positive = SVGDocument.from_psd(psdimage, text_letter_spacing_offset=0.5)
    tspan_positive = doc_positive.svg.find(".//tspan[@letter-spacing]")
    assert tspan_positive is not None
    letter_spacing_positive = float(tspan_positive.attrib.get("letter-spacing", "0"))
    assert abs(letter_spacing_positive - (letter_spacing_no_offset + 0.5)) < 1e-6

    # Test with negative offset
    doc_negative = SVGDocument.from_psd(psdimage, text_letter_spacing_offset=-0.3)
    tspan_negative = doc_negative.svg.find(".//tspan[@letter-spacing]")
    assert tspan_negative is not None
    letter_spacing_negative = float(tspan_negative.attrib.get("letter-spacing", "0"))
    assert abs(letter_spacing_negative - (letter_spacing_no_offset - 0.3)) < 1e-6


def test_text_letter_spacing_offset_zero_tracking() -> None:
    """Test text_letter_spacing_offset with text that has zero tracking."""
    # Use a text file - this should have zero tracking by default
    psdimage = PSDImage.open(
        get_fixture("texts/paragraph-shapetype0-justification0.psd")
    )

    # Test that offset is applied even when tracking is zero
    # First get baseline (no offset)
    doc_no_offset = SVGDocument.from_psd(psdimage, text_letter_spacing_offset=0.0)
    tspans_no_offset = doc_no_offset.svg.findall(".//tspan")

    # Apply offset and verify it's added to all text
    doc_with_offset = SVGDocument.from_psd(psdimage, text_letter_spacing_offset=-0.01)
    tspans_with_offset = doc_with_offset.svg.findall(".//tspan")

    # Both should have same number of tspans
    assert len(tspans_no_offset) == len(tspans_with_offset)

    # Check that the offset is properly applied
    for tspan_no, tspan_with in zip(tspans_no_offset, tspans_with_offset):
        if (
            tspan_no.text and tspan_no.text.strip()
        ):  # Only check tspans with actual text
            # Get letter-spacing values (default to 0 if not present)
            spacing_no = float(tspan_no.attrib.get("letter-spacing", "0"))
            spacing_with = float(tspan_with.attrib.get("letter-spacing", "0"))
            # The difference should be the offset (-0.01)
            assert abs((spacing_with - spacing_no) - (-0.01)) < 1e-6


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


def test_text_multiple_paragraphs_different_alignments() -> None:
    """Test that multiple paragraphs with different text anchors are handled correctly.

    Each paragraph has its own tspan with explicit positioning and text-anchor,
    regardless of whether the alignments differ or not. This provides consistent structure.
    """
    svg = convert_psd_to_svg("texts/paragraph-shapetype1-multiple.psd")
    text_node = svg.find(".//text")
    assert text_node is not None

    # The parent text node should not have x/y (each tspan has its own position)
    assert text_node.attrib.get("transform") is None, "Should use native positioning"

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


def test_text_japanese_notosans_cjk_jp() -> None:
    """Test Japanese text rendering.

    This test verifies that:
    1. Japanese text content is preserved in the SVG
    2. Text elements are properly created (not rasterized as an image)
    3. Font-family attribute is set (regardless of which font is used)

    Note: The PSD file specifies "NotoSansCJKjp-Regular" as the PostScript name.
    If the font is not installed, fontconfig will substitute an appropriate font
    that supports Japanese text.
    """
    svg = convert_psd_to_svg("texts/fonts-notosans-cjk-jp.psd")

    # Find all text elements
    text_nodes = svg.findall(".//text")
    assert len(text_nodes) > 0, "Should have at least one text element"

    # Check the first text element
    text_node = text_nodes[0]

    # Verify Japanese text content is preserved (美しい日本語 = Beautiful Japanese)
    text_content = "".join(text_node.itertext())
    assert "美しい日本語" in text_content, (
        f"Japanese text not found. Got: {text_content}"
    )

    # Verify font-family attribute is set (font substitution may occur)
    font_family = text_node.attrib.get("font-family")
    assert font_family is not None, "font-family should be set"


def test_text_japanese_with_custom_css() -> None:
    """Test Japanese text with custom CSS using append_css().

    This test verifies that:
    1. append_css() correctly injects CSS into the SVG
    2. The CSS rule is present in the final output
    3. Japanese text is properly rendered alongside custom CSS
    """
    psdimage = PSDImage.open(get_fixture("texts/fonts-notosans-cjk-jp.psd"))
    doc = SVGDocument.from_psd(psdimage)

    # Add CJK proportional width CSS
    doc.append_css("text { font-variant-east-asian: proportional-width; }")

    # Convert to string to check CSS injection
    svg_string = doc.tostring()

    # Verify CSS is present
    assert "<style>" in svg_string
    assert "font-variant-east-asian: proportional-width" in svg_string

    # Verify Japanese text is still present
    assert "美しい日本語" in svg_string

    # Verify text elements exist (not rasterized)
    # Parse the SVG and check for text elements
    svg_elem = ET.fromstring(svg_string.encode("utf-8"))
    # Use namespace-aware search for SVG elements
    ns = {"svg": "http://www.w3.org/2000/svg"}
    text_nodes = svg_elem.findall(".//svg:text", ns)
    assert len(text_nodes) > 0, "Should have at least one text element"


def test_text_wrapping_foreign_object_basic() -> None:
    """Test basic foreignObject text wrapping for bounding box text."""
    from psd2svg.core.text import TextWrappingMode

    psdimage = PSDImage.open(
        get_fixture("texts/paragraph-shapetype1-justification0.psd")
    )
    doc = SVGDocument.from_psd(
        psdimage, text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
    )

    # Should have foreignObject instead of text
    foreign_obj = doc.svg.find(".//foreignObject")
    assert foreign_obj is not None, "Should have foreignObject element"
    assert foreign_obj.attrib.get("width") is not None
    assert foreign_obj.attrib.get("height") is not None

    # Should have XHTML div with proper namespace
    div = foreign_obj.find(".//{http://www.w3.org/1999/xhtml}div")
    assert div is not None, "Should have XHTML div element"
    assert div.attrib.get("style") is not None

    # Should have XHTML paragraph
    p = div.find(".//{http://www.w3.org/1999/xhtml}p")
    assert p is not None, "Should have XHTML p element"


def test_text_wrapping_foreign_object_multiple_paragraphs() -> None:
    """Test foreignObject with multiple paragraphs."""
    from psd2svg.core.text import TextWrappingMode

    psdimage = PSDImage.open(get_fixture("texts/paragraph-shapetype1-multiple.psd"))
    doc = SVGDocument.from_psd(
        psdimage, text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
    )

    foreign_obj = doc.svg.find(".//foreignObject")
    assert foreign_obj is not None

    # Should have multiple <p> elements
    div = foreign_obj.find(".//{http://www.w3.org/1999/xhtml}div")
    assert div is not None
    paragraphs = div.findall(".//{http://www.w3.org/1999/xhtml}p")
    assert len(paragraphs) == 3, "Should have 3 paragraphs"


def test_text_wrapping_foreign_object_text_content() -> None:
    """Test that text content is preserved in foreignObject."""
    from psd2svg.core.text import TextWrappingMode

    psdimage = PSDImage.open(
        get_fixture("texts/paragraph-shapetype1-justification0.psd")
    )
    doc = SVGDocument.from_psd(
        psdimage, text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
    )

    # Extract all text from XHTML elements
    foreign_obj = doc.svg.find(".//foreignObject")
    assert foreign_obj is not None
    div = foreign_obj.find(".//{http://www.w3.org/1999/xhtml}div")
    assert div is not None
    text_content = "".join(div.itertext())

    # Should contain actual text (exact content depends on PSD file)
    assert len(text_content.strip()) > 0, "Should have text content"


def test_text_wrapping_point_text_unchanged() -> None:
    """Test that point text (ShapeType=0) uses native SVG even with foreignObject mode."""
    from psd2svg.core.text import TextWrappingMode

    psdimage = PSDImage.open(
        get_fixture("texts/paragraph-shapetype0-justification0.psd")
    )
    doc = SVGDocument.from_psd(
        psdimage, text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
    )

    # Point text should still use native <text> element
    text_node = doc.svg.find(".//text")
    assert text_node is not None, "Point text should use native SVG text"

    # Should NOT have foreignObject
    foreign_obj = doc.svg.find(".//foreignObject")
    assert foreign_obj is None, "Point text should not use foreignObject"


def test_text_wrapping_foreign_object_vertical() -> None:
    """Test foreignObject with vertical writing mode."""
    from psd2svg.core.text import TextWrappingMode

    psdimage = PSDImage.open(
        get_fixture(
            "texts/shapetype1-writingdirection2-baselinedirection2-justification0.psd"
        )
    )
    doc = SVGDocument.from_psd(
        psdimage, text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
    )

    foreign_obj = doc.svg.find(".//foreignObject")
    assert foreign_obj is not None

    # Check for vertical writing mode in container div
    div = foreign_obj.find(".//{http://www.w3.org/1999/xhtml}div")
    assert div is not None
    style = div.attrib.get("style", "")
    assert "writing-mode: vertical-rl" in style or "writing-mode:vertical-rl" in style
