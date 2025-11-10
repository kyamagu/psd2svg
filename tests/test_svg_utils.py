"""Tests for SVG utility functions."""

import pytest

from psd2svg import svg_utils


class TestNum2Str:
    """Test the num2str function for number formatting."""

    def test_boolean_true(self):
        """Test that boolean True converts to 'true'."""
        assert svg_utils.num2str(True) == "true"

    def test_boolean_false(self):
        """Test that boolean False converts to 'false'."""
        assert svg_utils.num2str(False) == "false"

    def test_integer(self):
        """Test that integers are converted to strings."""
        assert svg_utils.num2str(42) == "42"
        assert svg_utils.num2str(0) == "0"
        assert svg_utils.num2str(-100) == "-100"

    def test_integer_like_float(self):
        """Test that floats with integer values are formatted as integers."""
        assert svg_utils.num2str(1.0) == "1"
        assert svg_utils.num2str(100.0) == "100"
        assert svg_utils.num2str(-5.0) == "-5"

    def test_float_default_precision(self):
        """Test float formatting with default precision (2 digits)."""
        assert svg_utils.num2str(0.5) == "0.5"
        assert svg_utils.num2str(0.12) == "0.12"
        assert svg_utils.num2str(0.123) == "0.12"  # Rounded to 2 digits

    def test_float_trailing_zeros_removed(self):
        """Test that trailing zeros are removed."""
        assert svg_utils.num2str(0.10) == "0.1"
        assert svg_utils.num2str(1.50) == "1.5"
        assert svg_utils.num2str(0.100) == "0.1"

    def test_float_custom_precision(self):
        """Test float formatting with custom digit precision."""
        assert svg_utils.num2str(0.123456, digit=4) == "0.1235"  # Rounded
        assert svg_utils.num2str(0.123456, digit=6) == "0.123456"
        assert svg_utils.num2str(0.123456, digit=1) == "0.1"

    def test_no_scientific_notation_very_small(self):
        """Test that very small numbers don't use scientific notation."""
        # These would be 1e-05, 1e-06, etc. with 'g' format
        assert svg_utils.num2str(0.00001, digit=5) == "0.00001"
        assert svg_utils.num2str(0.000001, digit=6) == "0.000001"
        assert svg_utils.num2str(0.0000001, digit=7) == "0.0000001"

    def test_no_scientific_notation_very_large(self):
        """Test that large numbers don't use scientific notation."""
        assert svg_utils.num2str(1000000.0, digit=2) == "1000000"
        assert svg_utils.num2str(999999.99, digit=2) == "999999.99"
        assert svg_utils.num2str(123456.789, digit=3) == "123456.789"

    def test_negative_numbers(self):
        """Test formatting of negative numbers."""
        assert svg_utils.num2str(-0.5) == "-0.5"
        assert svg_utils.num2str(-0.123, digit=2) == "-0.12"
        assert svg_utils.num2str(-1.0) == "-1"

    def test_zero_variations(self):
        """Test various representations of zero."""
        assert svg_utils.num2str(0) == "0"
        assert svg_utils.num2str(0.0) == "0"
        assert svg_utils.num2str(-0.0) == "0"
        assert svg_utils.num2str(0.00, digit=4) == "0"

    def test_sign_preservation_on_small_negative(self):
        """Test that negative sign is preserved, even for very small values."""
        result = svg_utils.num2str(-0.00001, digit=5)
        assert result == "-0.00001"
        assert result[0] == "-"

    def test_rounding_behavior(self):
        """Test that rounding works correctly at boundaries."""
        assert svg_utils.num2str(0.125, digit=2) == "0.12"  # Rounds down
        assert svg_utils.num2str(0.126, digit=2) == "0.13"  # Rounds up
        assert svg_utils.num2str(0.995, digit=2) == "0.99"  # Truncated at 2 digits
        assert svg_utils.num2str(0.999, digit=2) == "1"  # Rounds to integer

    def test_invalid_type_raises_error(self):
        """Test that unsupported types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported type"):
            svg_utils.num2str("string")  # type: ignore
        with pytest.raises(ValueError, match="Unsupported type"):
            svg_utils.num2str([1, 2, 3])  # type: ignore


class TestSeq2Str:
    """Test the seq2str function for sequence formatting."""

    def test_empty_sequence(self):
        """Test that empty sequences produce empty strings."""
        assert svg_utils.seq2str([]) == ""

    def test_single_element(self):
        """Test formatting of single-element sequences."""
        assert svg_utils.seq2str([42]) == "42"
        assert svg_utils.seq2str([0.5]) == "0.5"
        assert svg_utils.seq2str([True]) == "true"

    def test_multiple_integers(self):
        """Test formatting of integer sequences."""
        assert svg_utils.seq2str([1, 2, 3]) == "1,2,3"
        assert svg_utils.seq2str([10, 20, 30, 40]) == "10,20,30,40"

    def test_multiple_floats(self):
        """Test formatting of float sequences."""
        assert svg_utils.seq2str([0.5, 1.5, 2.5]) == "0.5,1.5,2.5"
        assert svg_utils.seq2str([0.1, 0.2, 0.3]) == "0.1,0.2,0.3"

    def test_mixed_types(self):
        """Test formatting of sequences with mixed types."""
        assert svg_utils.seq2str([1, 0.5, 2]) == "1,0.5,2"
        assert svg_utils.seq2str([True, 0, 1.0]) == "true,0,1"

    def test_custom_separator(self):
        """Test formatting with custom separators."""
        assert svg_utils.seq2str([1, 2, 3], sep=" ") == "1 2 3"
        assert svg_utils.seq2str([0.5, 1.5], sep=";") == "0.5;1.5"
        assert svg_utils.seq2str([10, 20], sep=" , ") == "10 , 20"

    def test_custom_precision(self):
        """Test formatting with custom digit precision."""
        assert svg_utils.seq2str([0.123456, 0.789012], digit=4) == "0.1235,0.789"
        assert svg_utils.seq2str([0.1, 0.2, 0.3], digit=3) == "0.1,0.2,0.3"

    def test_custom_separator_and_precision(self):
        """Test formatting with both custom separator and precision."""
        assert svg_utils.seq2str([0.123, 0.456], sep=" ", digit=2) == "0.12 0.46"
        assert (
            svg_utils.seq2str([1.111, 2.222, 3.333], sep=",", digit=1) == "1.1,2.2,3.3"
        )

    def test_no_scientific_notation_in_sequence(self):
        """Test that no element in sequence uses scientific notation."""
        result = svg_utils.seq2str([0.00001, 0.00002, 0.00003], digit=5)
        assert result == "0.00001,0.00002,0.00003"
        assert "e" not in result.lower()  # No exponential notation

    def test_trailing_zeros_removed_in_sequence(self):
        """Test that trailing zeros are removed in sequences."""
        assert svg_utils.seq2str([1.0, 2.0, 3.0]) == "1,2,3"
        assert svg_utils.seq2str([0.10, 0.20, 0.30]) == "0.1,0.2,0.3"

    def test_matrix_transform_values(self):
        """Test formatting typical SVG matrix transform values."""
        # Typical matrix transform: a, b, c, d, e, f
        matrix = [1.0, 0.0, 0.0, 1.0, 100.5, 200.75]
        assert svg_utils.seq2str(matrix, sep=" ", digit=4) == "1 0 0 1 100.5 200.75"

    def test_coordinate_pairs(self):
        """Test formatting coordinate pairs as used in SVG."""
        coords = [10.5, 20.75, 30.25, 40.125]
        assert svg_utils.seq2str(coords, sep=" ", digit=3) == "10.5 20.75 30.25 40.125"

    def test_tuple_input(self):
        """Test that tuples work as well as lists."""
        assert svg_utils.seq2str((1, 2, 3)) == "1,2,3"
        assert svg_utils.seq2str((0.5, 1.5), sep=" ") == "0.5 1.5"


class TestSvgFormatting:
    """Integration tests for SVG-specific formatting scenarios."""

    def test_transform_translate(self):
        """Test formatting for SVG translate transform."""
        # translate(x, y)
        coords = (100.5, 200.75)
        assert svg_utils.seq2str(coords, sep=" ", digit=4) == "100.5 200.75"

    def test_transform_scale(self):
        """Test formatting for SVG scale transform."""
        # scale(sx, sy) - common case for gradient transforms
        scale = [0.5, 1.0]
        assert svg_utils.seq2str(scale, sep=" ", digit=4) == "0.5 1"

    def test_transform_matrix(self):
        """Test formatting for SVG matrix transform."""
        # matrix(a b c d e f)
        matrix = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        result = svg_utils.seq2str(matrix, sep=" ", digit=4)
        assert result == "1 0 0 1 0 0"
        # Ensure no scientific notation
        assert "e" not in result.lower()

    def test_opacity_values(self):
        """Test formatting for SVG opacity values."""
        # Opacity should be between 0 and 1
        assert svg_utils.num2str(0.5) == "0.5"
        assert svg_utils.num2str(0.75) == "0.75"
        assert svg_utils.num2str(1.0) == "1"
        assert svg_utils.num2str(0.0) == "0"

    def test_gradient_transform_with_very_small_scale(self):
        """Test that very small scale values don't produce scientific notation."""
        # This was the original bug - small values producing 1e-05
        small_scale = 0.00001
        result = svg_utils.num2str(small_scale, digit=5)
        assert result == "0.00001"
        assert "e" not in result.lower()
        assert "E" not in result

    def test_reference_point_coordinates(self):
        """Test formatting reference points for gradient transforms."""
        reference = (0.5, 0.5)
        assert svg_utils.seq2str(reference, sep=" ", digit=4) == "0.5 0.5"

        negative_reference = (-100.5, -200.75)
        assert (
            svg_utils.seq2str(negative_reference, sep=" ", digit=4) == "-100.5 -200.75"
        )
