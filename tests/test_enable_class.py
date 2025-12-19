"""Tests for enable_class flag functionality."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from psd_tools import PSDImage

from psd2svg import SVGDocument, convert
from psd2svg.core.converter import Converter

from tests.conftest import get_fixture

# Use a PSD file that definitely has layers with class attributes
TEST_PSD = "layer-types/invert.psd"


def test_enable_class_default_false() -> None:
    """Test that class attributes are omitted by default."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    document = SVGDocument.from_psd(psdimage)

    # Verify no class attributes exist by default
    elements_with_class = document.svg.findall(".//*[@class]")
    assert len(elements_with_class) == 0, "Should have no class attributes by default"


def test_enable_class_true_explicit() -> None:
    """Test that class attributes are included when explicitly enabled."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    document = SVGDocument.from_psd(psdimage, enable_class=True)

    # Find elements with class attributes
    elements_with_class = document.svg.findall(".//*[@class]")
    assert len(elements_with_class) > 0, "Should have elements with class attributes"


def test_enable_class_converter_direct() -> None:
    """Test enable_class flag at Converter level."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    converter = Converter(psdimage, enable_class=False)
    converter.build()

    elements_with_class = converter.svg.findall(".//*[@class]")
    assert len(elements_with_class) == 0, "Should have no class attributes"


def test_enable_class_converter_true() -> None:
    """Test enable_class flag at Converter level when enabled."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    converter = Converter(psdimage, enable_class=True)
    converter.build()

    elements_with_class = converter.svg.findall(".//*[@class]")
    assert len(elements_with_class) > 0, "Should have class attributes when enabled"


def test_enable_class_false_explicit() -> None:
    """Test explicit enable_class=False produces same result as default."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    doc_default = SVGDocument.from_psd(psdimage)
    doc_explicit_false = SVGDocument.from_psd(psdimage, enable_class=False)

    # Both should produce identical output with no class attributes
    default_classes = doc_default.svg.findall(".//*[@class]")
    explicit_classes = doc_explicit_false.svg.findall(".//*[@class]")

    assert len(default_classes) == 0
    assert len(explicit_classes) == 0
    assert len(default_classes) == len(explicit_classes)


def test_enable_class_with_layer_types() -> None:
    """Test that layer type classes (layer.kind) are controlled by the flag."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    # Without class attributes
    doc_without = SVGDocument.from_psd(psdimage, enable_class=False)
    elements_without = doc_without.svg.findall(".//*[@class]")

    # With class attributes
    doc_with = SVGDocument.from_psd(psdimage, enable_class=True)
    elements_with = doc_with.svg.findall(".//*[@class]")

    # Verify the difference
    assert len(elements_without) == 0
    assert len(elements_with) > 0

    # Check for specific layer type classes if present
    all_classes = " ".join([el.get("class", "") for el in elements_with])
    # Common layer types that might be present (including adjustment layers)
    possible_kinds = [
        "group",
        "pixel-layer",
        "shape-layer",
        "type-layer",
        "invert",
        "adjustment",
    ]
    has_layer_kind = any(kind in all_classes for kind in possible_kinds)
    if len(all_classes) > 0:
        assert has_layer_kind, f"Should have layer kind classes, got: {all_classes}"


def test_enable_class_convert_function(tmp_path: Path) -> None:
    """Test convert() function with enable_class parameter."""
    test_psd = get_fixture(TEST_PSD)
    output_without = tmp_path / "without_class.svg"
    output_with = tmp_path / "with_class.svg"

    # Convert without class attributes (default)
    convert(str(test_psd), str(output_without), enable_class=False)

    # Convert with class attributes
    convert(str(test_psd), str(output_with), enable_class=True)

    # Parse and verify
    tree_without = ET.parse(output_without)
    tree_with = ET.parse(output_with)

    elements_without = tree_without.findall(".//*[@class]")
    elements_with = tree_with.findall(".//*[@class]")

    assert len(elements_without) == 0
    assert len(elements_with) > 0


def test_enable_class_preserves_other_attributes() -> None:
    """Test that disabling class doesn't affect other attributes."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    doc_without_class = SVGDocument.from_psd(psdimage, enable_class=False)
    doc_with_class = SVGDocument.from_psd(psdimage, enable_class=True)

    # Check that other attributes are preserved (e.g., id, width, height)
    svg_without = doc_without_class.svg
    svg_with = doc_with_class.svg

    # SVG root should have width and height regardless of class flag
    assert svg_without.get("width") is not None
    assert svg_without.get("height") is not None
    assert svg_with.get("width") is not None
    assert svg_with.get("height") is not None

    # Dimensions should be the same
    assert svg_without.get("width") == svg_with.get("width")
    assert svg_without.get("height") == svg_with.get("height")


def test_enable_class_with_multiple_layers() -> None:
    """Test enable_class with a PSD containing multiple layers."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    # Test with layers if available
    if len(psdimage) == 0:
        pytest.skip("No layers in test PSD")

    doc_with_class = SVGDocument.from_psd(psdimage, enable_class=True)
    elements_with_class = doc_with_class.svg.findall(".//*[@class]")

    # Should have class attributes for multiple layers
    assert len(elements_with_class) > 0

    doc_without_class = SVGDocument.from_psd(psdimage, enable_class=False)
    elements_without_class = doc_without_class.svg.findall(".//*[@class]")

    # Should have no class attributes
    assert len(elements_without_class) == 0


def test_enable_class_independence_from_title() -> None:
    """Test that enable_class works independently from enable_title."""
    psdimage = PSDImage.open(get_fixture(TEST_PSD))
    # Test all combinations
    doc_both_false = SVGDocument.from_psd(
        psdimage, enable_class=False, enable_title=False
    )
    doc_class_only = SVGDocument.from_psd(
        psdimage, enable_class=True, enable_title=False
    )
    doc_title_only = SVGDocument.from_psd(
        psdimage, enable_class=False, enable_title=True
    )
    doc_both_true = SVGDocument.from_psd(psdimage, enable_class=True, enable_title=True)

    # Verify class attributes
    assert len(doc_both_false.svg.findall(".//*[@class]")) == 0
    assert len(doc_title_only.svg.findall(".//*[@class]")) == 0
    # class_only and both_true should have class attributes if there are layers
    class_only_count = len(doc_class_only.svg.findall(".//*[@class]"))
    both_true_count = len(doc_both_true.svg.findall(".//*[@class]"))
    # Both should have same number of class attributes
    assert class_only_count == both_true_count

    # Verify title elements
    assert len(doc_both_false.svg.findall(".//title")) == 0
    assert len(doc_class_only.svg.findall(".//title")) == 0
    # title_only and both_true should have title elements if there are layers
    title_only_count = len(doc_title_only.svg.findall(".//title"))
    both_true_count_titles = len(doc_both_true.svg.findall(".//title"))
    # Both should have same number of title elements
    assert title_only_count == both_true_count_titles
