"""Tests for SVG utility functions."""

import xml.etree.ElementTree as ET

import pytest

from psd2svg import svg_utils


class TestNum2Str:
    """Test the num2str function for number formatting."""

    def test_boolean_true(self) -> None:
        """Test that boolean True converts to 'true'."""
        assert svg_utils.num2str(True) == "true"

    def test_boolean_false(self) -> None:
        """Test that boolean False converts to 'false'."""
        assert svg_utils.num2str(False) == "false"

    def test_integer(self) -> None:
        """Test that integers are converted to strings."""
        assert svg_utils.num2str(42) == "42"
        assert svg_utils.num2str(0) == "0"
        assert svg_utils.num2str(-100) == "-100"

    def test_integer_like_float(self) -> None:
        """Test that floats with integer values are formatted as integers."""
        assert svg_utils.num2str(1.0) == "1"
        assert svg_utils.num2str(100.0) == "100"
        assert svg_utils.num2str(-5.0) == "-5"

    def test_float_default_precision(self) -> None:
        """Test float formatting with default precision (2 digits)."""
        assert svg_utils.num2str(0.5) == "0.5"
        assert svg_utils.num2str(0.12) == "0.12"
        assert svg_utils.num2str(0.123) == "0.12"  # Rounded to 2 digits

    def test_float_trailing_zeros_removed(self) -> None:
        """Test that trailing zeros are removed."""
        assert svg_utils.num2str(0.10) == "0.1"
        assert svg_utils.num2str(1.50) == "1.5"
        assert svg_utils.num2str(0.100) == "0.1"

    def test_float_custom_precision(self) -> None:
        """Test float formatting with custom digit precision."""
        assert svg_utils.num2str(0.123456, digit=4) == "0.1235"  # Rounded
        assert svg_utils.num2str(0.123456, digit=6) == "0.123456"
        assert svg_utils.num2str(0.123456, digit=1) == "0.1"

    def test_no_scientific_notation_very_small(self) -> None:
        """Test that very small numbers don't use scientific notation."""
        # These would be 1e-05, 1e-06, etc. with 'g' format
        assert svg_utils.num2str(0.00001, digit=5) == "0.00001"
        assert svg_utils.num2str(0.000001, digit=6) == "0.000001"
        assert svg_utils.num2str(0.0000001, digit=7) == "0.0000001"

    def test_no_scientific_notation_very_large(self) -> None:
        """Test that large numbers don't use scientific notation."""
        assert svg_utils.num2str(1000000.0, digit=2) == "1000000"
        assert svg_utils.num2str(999999.99, digit=2) == "999999.99"
        assert svg_utils.num2str(123456.789, digit=3) == "123456.789"

    def test_negative_numbers(self) -> None:
        """Test formatting of negative numbers."""
        assert svg_utils.num2str(-0.5) == "-0.5"
        assert svg_utils.num2str(-0.123, digit=2) == "-0.12"
        assert svg_utils.num2str(-1.0) == "-1"

    def test_zero_variations(self) -> None:
        """Test various representations of zero."""
        assert svg_utils.num2str(0) == "0"
        assert svg_utils.num2str(0.0) == "0"
        assert svg_utils.num2str(-0.0) == "0"
        assert svg_utils.num2str(0.00, digit=4) == "0"

    def test_sign_preservation_on_small_negative(self) -> None:
        """Test that negative sign is preserved, even for very small values."""
        result = svg_utils.num2str(-0.00001, digit=5)
        assert result == "-0.00001"
        assert result[0] == "-"

    def test_rounding_behavior(self) -> None:
        """Test that rounding works correctly at boundaries."""
        assert svg_utils.num2str(0.125, digit=2) == "0.12"  # Rounds down
        assert svg_utils.num2str(0.126, digit=2) == "0.13"  # Rounds up
        assert svg_utils.num2str(0.995, digit=2) == "0.99"  # Truncated at 2 digits
        assert svg_utils.num2str(0.999, digit=2) == "1"  # Rounds to integer

    def test_invalid_type_raises_error(self) -> None:
        """Test that unsupported types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported type"):
            svg_utils.num2str("string")  # type: ignore
        with pytest.raises(ValueError, match="Unsupported type"):
            svg_utils.num2str([1, 2, 3])  # type: ignore


class TestSeq2Str:
    """Test the seq2str function for sequence formatting."""

    def test_empty_sequence(self) -> None:
        """Test that empty sequences produce empty strings."""
        assert svg_utils.seq2str([]) == ""

    def test_single_element(self) -> None:
        """Test formatting of single-element sequences."""
        assert svg_utils.seq2str([42]) == "42"
        assert svg_utils.seq2str([0.5]) == "0.5"
        assert svg_utils.seq2str([True]) == "true"

    def test_multiple_integers(self) -> None:
        """Test formatting of integer sequences."""
        assert svg_utils.seq2str([1, 2, 3]) == "1,2,3"
        assert svg_utils.seq2str([10, 20, 30, 40]) == "10,20,30,40"

    def test_multiple_floats(self) -> None:
        """Test formatting of float sequences."""
        assert svg_utils.seq2str([0.5, 1.5, 2.5]) == "0.5,1.5,2.5"
        assert svg_utils.seq2str([0.1, 0.2, 0.3]) == "0.1,0.2,0.3"

    def test_mixed_types(self) -> None:
        """Test formatting of sequences with mixed types."""
        assert svg_utils.seq2str([1, 0.5, 2]) == "1,0.5,2"
        assert svg_utils.seq2str([True, 0, 1.0]) == "true,0,1"

    def test_custom_separator(self) -> None:
        """Test formatting with custom separators."""
        assert svg_utils.seq2str([1, 2, 3], sep=" ") == "1 2 3"
        assert svg_utils.seq2str([0.5, 1.5], sep=";") == "0.5;1.5"
        assert svg_utils.seq2str([10, 20], sep=" , ") == "10 , 20"

    def test_custom_precision(self) -> None:
        """Test formatting with custom digit precision."""
        assert svg_utils.seq2str([0.123456, 0.789012], digit=4) == "0.1235,0.789"
        assert svg_utils.seq2str([0.1, 0.2, 0.3], digit=3) == "0.1,0.2,0.3"

    def test_custom_separator_and_precision(self) -> None:
        """Test formatting with both custom separator and precision."""
        assert svg_utils.seq2str([0.123, 0.456], sep=" ", digit=2) == "0.12 0.46"
        assert (
            svg_utils.seq2str([1.111, 2.222, 3.333], sep=",", digit=1) == "1.1,2.2,3.3"
        )

    def test_no_scientific_notation_in_sequence(self) -> None:
        """Test that no element in sequence uses scientific notation."""
        result = svg_utils.seq2str([0.00001, 0.00002, 0.00003], digit=5)
        assert result == "0.00001,0.00002,0.00003"
        assert "e" not in result.lower()  # No exponential notation

    def test_trailing_zeros_removed_in_sequence(self) -> None:
        """Test that trailing zeros are removed in sequences."""
        assert svg_utils.seq2str([1.0, 2.0, 3.0]) == "1,2,3"
        assert svg_utils.seq2str([0.10, 0.20, 0.30]) == "0.1,0.2,0.3"

    def test_matrix_transform_values(self) -> None:
        """Test formatting typical SVG matrix transform values."""
        # Typical matrix transform: a, b, c, d, e, f
        matrix = [1.0, 0.0, 0.0, 1.0, 100.5, 200.75]
        assert svg_utils.seq2str(matrix, sep=" ", digit=4) == "1 0 0 1 100.5 200.75"

    def test_coordinate_pairs(self) -> None:
        """Test formatting coordinate pairs as used in SVG."""
        coords = [10.5, 20.75, 30.25, 40.125]
        assert svg_utils.seq2str(coords, sep=" ", digit=3) == "10.5 20.75 30.25 40.125"

    def test_tuple_input(self) -> None:
        """Test that tuples work as well as lists."""
        assert svg_utils.seq2str((1, 2, 3)) == "1,2,3"
        assert svg_utils.seq2str((0.5, 1.5), sep=" ") == "0.5 1.5"


class TestSvgFormatting:
    """Integration tests for SVG-specific formatting scenarios."""

    def test_transform_translate(self) -> None:
        """Test formatting for SVG translate transform."""
        # translate(x, y)
        coords = (100.5, 200.75)
        assert svg_utils.seq2str(coords, sep=" ", digit=4) == "100.5 200.75"

    def test_transform_scale(self) -> None:
        """Test formatting for SVG scale transform."""
        # scale(sx, sy) - common case for gradient transforms
        scale = [0.5, 1.0]
        assert svg_utils.seq2str(scale, sep=" ", digit=4) == "0.5 1"

    def test_transform_matrix(self) -> None:
        """Test formatting for SVG matrix transform."""
        # matrix(a b c d e f)
        matrix = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        result = svg_utils.seq2str(matrix, sep=" ", digit=4)
        assert result == "1 0 0 1 0 0"
        # Ensure no scientific notation
        assert "e" not in result.lower()

    def test_opacity_values(self) -> None:
        """Test formatting for SVG opacity values."""
        # Opacity should be between 0 and 1
        assert svg_utils.num2str(0.5) == "0.5"
        assert svg_utils.num2str(0.75) == "0.75"
        assert svg_utils.num2str(1.0) == "1"
        assert svg_utils.num2str(0.0) == "0"

    def test_gradient_transform_with_very_small_scale(self) -> None:
        """Test that very small scale values don't produce scientific notation."""
        # This was the original bug - small values producing 1e-05
        small_scale = 0.00001
        result = svg_utils.num2str(small_scale, digit=5)
        assert result == "0.00001"
        assert "e" not in result.lower()
        assert "E" not in result

    def test_reference_point_coordinates(self) -> None:
        """Test formatting reference points for gradient transforms."""
        reference = (0.5, 0.5)
        assert svg_utils.seq2str(reference, sep=" ", digit=4) == "0.5 0.5"

        negative_reference = (-100.5, -200.75)
        assert (
            svg_utils.seq2str(negative_reference, sep=" ", digit=4) == "-100.5 -200.75"
        )


class TestMergeAttributeLessChildren:
    """Test the merge_attribute_less_children function."""

    def test_simple_attribute_less_children(self) -> None:
        """Test merging simple children without attributes."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan")
        tspan1.text = "Hello"
        tspan2 = ET.SubElement(text, "tspan")  # No attributes
        tspan2.text = " World"

        svg_utils.merge_attribute_less_children(text)

        # Both tspans should be merged into parent text
        assert len(text) == 0
        assert text.text == "Hello World"

    def test_preserve_order_with_styled_elements(self) -> None:
        """Test that text order is preserved when merging around styled elements."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        tspan1.text = "Bold"
        tspan2 = ET.SubElement(text, "tspan")  # No attributes
        tspan2.text = " Regular"

        svg_utils.merge_attribute_less_children(text)

        # Should have one child (the bold tspan) with text after it
        assert len(text) == 1
        assert text[0].attrib.get("font-weight") == "700"
        assert text[0].text == "Bold"
        assert text[0].tail == " Regular"

    def test_nested_attribute_less_children(self) -> None:
        """Test merging nested children without attributes."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"x": "10"})
        tspan2 = ET.SubElement(tspan1, "tspan")  # No attributes, nested
        tspan2.text = "Nested text"

        svg_utils.merge_attribute_less_children(text)

        # Nested tspan should be merged into parent tspan
        assert len(text) == 1
        assert text[0].attrib.get("x") == "10"
        assert len(text[0]) == 0  # No children
        assert text[0].text == "Nested text"

    def test_multiple_attribute_less_between_styled(self) -> None:
        """Test multiple attribute-less children between styled elements."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        tspan1.text = "Bold"
        tspan2 = ET.SubElement(text, "tspan")  # No attributes
        tspan2.text = " and "
        tspan3 = ET.SubElement(text, "tspan", attrib={"font-style": "italic"})
        tspan3.text = "italic"

        svg_utils.merge_attribute_less_children(text)

        # Should have two children (bold and italic) with text between them
        assert len(text) == 2
        assert text[0].attrib.get("font-weight") == "700"
        assert text[0].text == "Bold"
        assert text[0].tail == " and "
        assert text[1].attrib.get("font-style") == "italic"
        assert text[1].text == "italic"

    def test_all_children_have_attributes(self) -> None:
        """Test that nothing changes when all children have attributes."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        tspan1.text = "Bold"
        tspan2 = ET.SubElement(text, "tspan", attrib={"font-style": "italic"})
        tspan2.text = "Italic"

        svg_utils.merge_attribute_less_children(text)

        # Nothing should change
        assert len(text) == 2
        assert text[0].attrib.get("font-weight") == "700"
        assert text[0].text == "Bold"
        assert text[1].attrib.get("font-style") == "italic"
        assert text[1].text == "Italic"

    def test_first_child_without_attributes(self) -> None:
        """Test merging when first child has no attributes."""

        text = ET.Element("text")
        text.text = "Start "
        tspan1 = ET.SubElement(text, "tspan")  # No attributes
        tspan1.text = "Middle"
        tspan2 = ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        tspan2.text = "End"

        svg_utils.merge_attribute_less_children(text)

        # First tspan should merge into parent text
        assert len(text) == 1
        assert text.text == "Start Middle"
        assert text[0].attrib.get("font-weight") == "700"
        assert text[0].text == "End"

    def test_tail_handling(self) -> None:
        """Test that tail text is properly preserved."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        tspan1.text = "Bold"
        tspan2 = ET.SubElement(text, "tspan")  # No attributes
        tspan2.text = "Regular"
        tspan2.tail = " after"

        svg_utils.merge_attribute_less_children(text)

        # The tail should be preserved
        assert len(text) == 1
        assert text[0].tail == "Regular after"

    def test_empty_attribute_less_children(self) -> None:
        """Test merging children with no text content."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"x": "10"})
        tspan1.text = "Text"
        ET.SubElement(text, "tspan")  # No attributes, no text - will be removed
        tspan3 = ET.SubElement(text, "tspan", attrib={"y": "20"})
        tspan3.text = "More"

        svg_utils.merge_attribute_less_children(text)

        # Empty tspan should be removed
        assert len(text) == 2
        assert text[0].attrib.get("x") == "10"
        assert text[1].attrib.get("y") == "20"

    def test_deeply_nested_structure(self) -> None:
        """Test merging in deeply nested structures."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"x": "10"})
        tspan2 = ET.SubElement(tspan1, "tspan", attrib={"font-weight": "700"})
        tspan3 = ET.SubElement(tspan2, "tspan")  # No attributes
        tspan3.text = "Deep text"

        svg_utils.merge_attribute_less_children(text)

        # Should recursively merge from innermost to outermost
        assert len(text) == 1
        assert len(text[0]) == 1
        assert len(text[0][0]) == 0
        assert text[0][0].text == "Deep text"

    def test_complex_real_world_scenario(self) -> None:
        """Test a complex real-world SVG text structure."""

        # Simulate: <text>First <tspan font-weight="700">bold</tspan> then <tspan>normal</tspan> end</text>
        text = ET.Element("text")
        text.text = "First "
        tspan1 = ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        tspan1.text = "bold"
        tspan1.tail = " then "
        tspan2 = ET.SubElement(text, "tspan")  # No attributes
        tspan2.text = "normal"
        tspan2.tail = " end"

        svg_utils.merge_attribute_less_children(text)

        # tspan2 should be merged, preserving all text
        assert len(text) == 1
        assert text.text == "First "
        assert text[0].text == "bold"
        assert text[0].tail == " then normal end"

    def test_attribute_less_child_with_nested_children(self) -> None:
        """Test that attribute-less children with nested elements are unwrapped.

        This is a regression test for a bug where attribute-less children
        would be merged even if they contained nested elements, causing
        those nested elements to be lost.

        Now it unwraps them: moves the nested children up to the parent level.
        """
        # Create: <text><tspan><tspan font-size="18">A</tspan><tspan font-size="20">B</tspan></tspan></text>
        text = ET.Element("text")
        outer_tspan = ET.SubElement(text, "tspan")  # No attributes

        inner1 = ET.SubElement(outer_tspan, "tspan", attrib={"font-size": "18"})
        inner1.text = "A"

        inner2 = ET.SubElement(outer_tspan, "tspan", attrib={"font-size": "20"})
        inner2.text = "B"

        svg_utils.merge_attribute_less_children(text)

        # outer_tspan should be unwrapped - its children moved up to text
        assert len(text) == 2
        assert text[0].attrib.get("font-size") == "18"
        assert text[0].text == "A"
        assert text[1].attrib.get("font-size") == "20"
        assert text[1].text == "B"

    def test_mixed_attribute_less_with_nested(self) -> None:
        """Test mixed scenario with attribute-less children, some with nested elements."""
        # <text><tspan font-weight="700">Bold</tspan><tspan><tspan font-size="18">Nested</tspan></tspan></text>
        text = ET.Element("text")

        tspan1 = ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        tspan1.text = "Bold"

        tspan2 = ET.SubElement(text, "tspan")  # No attributes
        inner = ET.SubElement(tspan2, "tspan", attrib={"font-size": "18"})
        inner.text = "Nested"

        svg_utils.merge_attribute_less_children(text)

        # tspan2 should be unwrapped - inner moved up to text level
        assert len(text) == 2
        assert text[0].text == "Bold"
        assert text[1].attrib.get("font-size") == "18"
        assert text[1].text == "Nested"


class TestMergeCommonChildAttributes:
    """Tests for merge_common_child_attributes utility function."""

    def test_simple_common_attributes(self) -> None:
        """Test merging common attributes from all children."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"fill": "red", "font-size": "12"})
        tspan1.text = "A"
        tspan2 = ET.SubElement(text, "tspan", attrib={"fill": "red", "font-size": "12"})
        tspan2.text = "B"

        svg_utils.merge_common_child_attributes(text)

        # Common attributes should be hoisted to parent
        assert text.attrib.get("fill") == "red"
        assert text.attrib.get("font-size") == "12"
        # Children should have attributes removed
        assert "fill" not in tspan1.attrib
        assert "font-size" not in tspan1.attrib
        assert "fill" not in tspan2.attrib
        assert "font-size" not in tspan2.attrib

    def test_partial_common_attributes(self) -> None:
        """Test that only truly common attributes are hoisted."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"fill": "red", "font-size": "12"})
        tspan1.text = "A"
        tspan2 = ET.SubElement(text, "tspan", attrib={"fill": "red", "font-size": "14"})
        tspan2.text = "B"

        svg_utils.merge_common_child_attributes(text)

        # Only fill is common, font-size differs
        assert text.attrib.get("fill") == "red"
        assert "font-size" not in text.attrib
        # Children should keep differing attributes
        assert "fill" not in tspan1.attrib
        assert tspan1.attrib.get("font-size") == "12"
        assert "fill" not in tspan2.attrib
        assert tspan2.attrib.get("font-size") == "14"

    def test_no_common_attributes(self) -> None:
        """Test when no attributes are common."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan", attrib={"fill": "red"})
        tspan1.text = "A"
        tspan2 = ET.SubElement(text, "tspan", attrib={"font-size": "12"})
        tspan2.text = "B"

        svg_utils.merge_common_child_attributes(text)

        # No common attributes, parent should be unchanged
        assert "fill" not in text.attrib
        assert "font-size" not in text.attrib
        # Children should keep their attributes
        assert tspan1.attrib.get("fill") == "red"
        assert tspan2.attrib.get("font-size") == "12"

    def test_excludes_parameter(self) -> None:
        """Test that excluded attributes are not hoisted."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(
            text, "tspan", attrib={"x": "10", "y": "20", "fill": "red"}
        )
        tspan1.text = "A"
        tspan2 = ET.SubElement(
            text, "tspan", attrib={"x": "30", "y": "20", "fill": "red"}
        )
        tspan2.text = "B"

        svg_utils.merge_common_child_attributes(text, excludes={"x", "y"})

        # fill should be hoisted, x and y should not
        assert text.attrib.get("fill") == "red"
        assert "x" not in text.attrib
        assert "y" not in text.attrib
        # Children should keep excluded attributes
        assert tspan1.attrib.get("x") == "10"
        assert tspan1.attrib.get("y") == "20"
        assert tspan2.attrib.get("x") == "30"
        assert tspan2.attrib.get("y") == "20"
        assert "fill" not in tspan1.attrib
        assert "fill" not in tspan2.attrib

    def test_recursive_processing(self) -> None:
        """Test that function processes nested children recursively."""

        text = ET.Element("text")
        g1 = ET.SubElement(text, "g")
        tspan1 = ET.SubElement(g1, "tspan", attrib={"fill": "red"})
        tspan1.text = "A"
        tspan2 = ET.SubElement(g1, "tspan", attrib={"fill": "red"})
        tspan2.text = "B"
        g2 = ET.SubElement(text, "g")
        tspan3 = ET.SubElement(g2, "tspan", attrib={"fill": "red"})
        tspan3.text = "C"

        svg_utils.merge_common_child_attributes(text)

        # Common attribute should be hoisted all the way to text
        # since all nested tspans have fill="red"
        assert text.attrib.get("fill") == "red"
        assert "fill" not in g1.attrib
        assert "fill" not in g2.attrib
        assert "fill" not in tspan1.attrib
        assert "fill" not in tspan2.attrib
        assert "fill" not in tspan3.attrib

    def test_empty_element(self) -> None:
        """Test with element that has no children."""

        text = ET.Element("text")
        text.text = "No children"

        # Should not raise an error
        svg_utils.merge_common_child_attributes(text)

        assert text.text == "No children"
        assert len(text.attrib) == 0

    def test_single_child(self) -> None:
        """Test with element that has only one child."""

        text = ET.Element("text")
        tspan = ET.SubElement(text, "tspan", attrib={"fill": "red"})
        tspan.text = "Only child"

        svg_utils.merge_common_child_attributes(text)

        # Single child's attributes should be hoisted
        assert text.attrib.get("fill") == "red"
        assert "fill" not in tspan.attrib


class TestMergeSingletonChildren:
    """Tests for merge_singleton_children utility function."""

    def test_simple_singleton_merge(self) -> None:
        """Test merging a simple singleton child."""

        text = ET.Element("text")
        tspan = ET.SubElement(text, "tspan")
        tspan.text = "Hello"

        svg_utils.merge_singleton_children(text)

        # Singleton child should be merged into parent
        assert len(text) == 0
        assert text.text == "Hello"

    def test_singleton_with_attributes(self) -> None:
        """Test merging singleton child with attributes."""

        text = ET.Element("text", attrib={"x": "10"})
        tspan = ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        tspan.text = "Bold"

        svg_utils.merge_singleton_children(text)

        # Child's attributes should be moved to parent
        assert len(text) == 0
        assert text.text == "Bold"
        assert text.attrib.get("x") == "10"
        assert text.attrib.get("font-weight") == "700"

    def test_conflicting_attributes_no_merge(self) -> None:
        """Test that singleton with conflicting attributes is not merged."""

        text = ET.Element("text", attrib={"x": "10"})
        tspan = ET.SubElement(text, "tspan", attrib={"x": "20"})
        tspan.text = "Text"

        svg_utils.merge_singleton_children(text)

        # Should not merge due to conflicting 'x' attribute
        assert len(text) == 1
        assert text[0] is tspan
        assert text.attrib.get("x") == "10"
        assert tspan.attrib.get("x") == "20"

    def test_singleton_with_tail(self) -> None:
        """Test that singleton's tail is properly handled."""

        # Create: <g><text>Hello</text> World</g>
        g = ET.Element("g")
        text = ET.SubElement(g, "text")
        text.text = "Hello"
        text.tail = " World"

        svg_utils.merge_singleton_children(g)

        # The tail should become part of parent's text
        assert len(g) == 0
        assert g.text == "Hello World"

    def test_multiple_children_no_merge(self) -> None:
        """Test that element with multiple children is not merged."""

        text = ET.Element("text")
        tspan1 = ET.SubElement(text, "tspan")
        tspan1.text = "A"
        tspan2 = ET.SubElement(text, "tspan")
        tspan2.text = "B"

        svg_utils.merge_singleton_children(text)

        # Should not merge, still has two children
        assert len(text) == 2
        assert text[0] is tspan1
        assert text[1] is tspan2

    def test_recursive_processing(self) -> None:
        """Test that function processes nested singletons recursively."""

        # Create: <text><g><tspan>Hello</tspan></g></text>
        text = ET.Element("text")
        g = ET.SubElement(text, "g")
        tspan = ET.SubElement(g, "tspan")
        tspan.text = "Hello"

        svg_utils.merge_singleton_children(text)

        # Should merge both levels: tspan into g, then g into text
        assert len(text) == 0
        assert text.text == "Hello"

    def test_parent_with_existing_text(self) -> None:
        """Test merging when parent already has text."""

        text = ET.Element("text")
        text.text = "Start "
        tspan = ET.SubElement(text, "tspan")
        tspan.text = "End"

        svg_utils.merge_singleton_children(text)

        # Child's text should be appended to parent's text
        assert len(text) == 0
        assert text.text == "Start End"

    def test_parent_with_text_and_child_with_tail(self) -> None:
        """Test complex case with both parent text and child tail."""

        # This is unusual but possible: <text>Before<tspan>Middle</tspan>After</text>
        text = ET.Element("text")
        text.text = "Before"
        tspan = ET.SubElement(text, "tspan")
        tspan.text = "Middle"
        tspan.tail = "After"

        svg_utils.merge_singleton_children(text)

        # All text should be merged in document order
        assert len(text) == 0
        assert text.text == "BeforeMiddleAfter"

    def test_empty_singleton_child(self) -> None:
        """Test merging an empty singleton child."""

        text = ET.Element("text")
        ET.SubElement(text, "tspan", attrib={"font-weight": "700"})
        # No text in tspan

        svg_utils.merge_singleton_children(text)

        # Empty child should still be merged, attributes moved
        assert len(text) == 0
        assert text.text is None
        assert text.attrib.get("font-weight") == "700"

    def test_multi_child_parent_with_nested_singletons(self) -> None:
        """Test that parent with multiple children is not merged even when nested children are singletons.

        This is a regression test for a bug where recursive processing would merge
        nested singletons first, reducing the parent's child count and causing it
        to be incorrectly merged.
        """
        # Create structure: <text><tspan><tspan>A</tspan><tspan>B</tspan></tspan></text>
        # The outer tspan has 2 children initially, so it shouldn't be merged
        # But if we process recursively first, both inner tspans might disappear
        text = ET.Element(
            "text",
            attrib={
                "transform": "matrix(3.36,0,-0.68,3.35,253.68,244.16)",
                "font-family": "Kozuka Gothic Pr6N",
                "font-weight": "700",
                "fill": "#0000ff",
            },
        )
        outer_tspan = ET.SubElement(text, "tspan")

        # Add multiple inner tspans
        tspan1 = ET.SubElement(
            outer_tspan,
            "tspan",
            attrib={
                "font-size": "18",
                "baseline-shift": "-0.36",
                "letter-spacing": "0.72",
            },
        )
        tspan1.text = "さ"

        tspan2 = ET.SubElement(
            outer_tspan, "tspan", attrib={"font-size": "18", "letter-spacing": "0.72"}
        )
        tspan2.text = "す"

        tspan3 = ET.SubElement(
            outer_tspan, "tspan", attrib={"font-size": "18", "letter-spacing": "0.72"}
        )
        tspan3.text = "だ"

        tspan4 = ET.SubElement(
            outer_tspan, "tspan", attrib={"font-size": "18", "letter-spacing": "0.72"}
        )
        tspan4.text = "け"

        tspan5 = ET.SubElement(
            outer_tspan,
            "tspan",
            attrib={
                "font-size": "20.85",
                "baseline-shift": "-0.36",
                "letter-spacing": "0.83",
            },
        )
        tspan5.text = "！"

        ET.SubElement(
            outer_tspan,
            "tspan",
            attrib={
                "font-size": "20.85",
                "baseline-shift": "-0.36",
                "letter-spacing": "0.83",
            },
        )
        # Last tspan has no text (empty)

        svg_utils.merge_singleton_children(text)

        # The outer tspan wrapper should be unwrapped, moving its children directly under text
        assert len(text) == 6  # Now has 6 direct children (the inner tspans)

        # The inner tspans should be direct children of text now
        assert text[0].text == "さ"
        assert text[1].text == "す"
        assert text[2].text == "だ"
        assert text[3].text == "け"
        assert text[4].text == "！"
        assert text[5].text is None  # Empty tspan

    def test_unwrap_singleton_with_nested_children(self) -> None:
        """Test that singleton wrappers without attributes are unwrapped."""
        # <text><tspan><tspan baseline-shift="-0.36">A</tspan><tspan letter-spacing="0.72">B</tspan></tspan></text>
        text = ET.Element("text")
        outer_tspan = ET.SubElement(text, "tspan")  # No attributes, no text
        inner1 = ET.SubElement(outer_tspan, "tspan", attrib={"baseline-shift": "-0.36"})
        inner1.text = "A"
        inner2 = ET.SubElement(outer_tspan, "tspan", attrib={"letter-spacing": "0.72"})
        inner2.text = "B"

        svg_utils.merge_singleton_children(text)

        # outer_tspan should be unwrapped - its children moved up to text
        assert len(text) == 2
        assert text[0].attrib.get("baseline-shift") == "-0.36"
        assert text[0].text == "A"
        assert text[1].attrib.get("letter-spacing") == "0.72"
        assert text[1].text == "B"

    def test_unwrap_singleton_with_attributes(self) -> None:
        """Test that singleton wrappers with attributes are unwrapped and attributes moved to parent."""
        # <text><tspan fill="red"><tspan>A</tspan><tspan>B</tspan></tspan></text>
        text = ET.Element("text")
        outer_tspan = ET.SubElement(text, "tspan", attrib={"fill": "red"})
        inner1 = ET.SubElement(outer_tspan, "tspan")
        inner1.text = "A"
        inner2 = ET.SubElement(outer_tspan, "tspan")
        inner2.text = "B"

        svg_utils.merge_singleton_children(text)

        # outer_tspan should be unwrapped, fill moved to text
        assert len(text) == 2
        assert text.attrib.get("fill") == "red"
        assert text[0].text == "A"
        assert text[1].text == "B"
