"""Tests for psd2svg.core.font_utils module."""

import logging
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from psd2svg.core.font_utils import FontInfo


class TestFontInfo:
    """Tests for FontInfo dataclass."""

    def test_init(self) -> None:
        """Test FontInfo initialization."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        assert font.postscript_name == "ArialMT"
        assert font.file == "/path/to/arial.ttf"
        assert font.family == "Arial"
        assert font.style == "Regular"
        assert font.weight == 80.0

    def test_family_name_property(self) -> None:
        """Test family_name property returns family name."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        assert font.family_name == "Arial"

    def test_family_name_property_empty(self) -> None:
        """Test family_name property with empty family string."""
        font = FontInfo(
            postscript_name="UnknownFont",
            file="/path/to/unknown.ttf",
            family="",
            style="Regular",
            weight=80.0,
        )
        assert font.family_name == ""

    def test_bold_property_regular_weight(self) -> None:
        """Test bold property returns False for regular weight."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        assert font.bold is False

    def test_bold_property_bold_weight(self) -> None:
        """Test bold property returns True for bold weight (>= 200)."""
        font = FontInfo(
            postscript_name="Arial-BoldMT",
            file="/path/to/arial-bold.ttf",
            family="Arial",
            style="Bold",
            weight=200.0,
        )
        assert font.bold is True

    def test_bold_property_edge_case(self) -> None:
        """Test bold property at weight boundary."""
        # Weight exactly 200 should be bold
        font = FontInfo(
            postscript_name="Arial-BoldMT",
            file="/path/to/arial-bold.ttf",
            family="Arial",
            style="Bold",
            weight=200.0,
        )
        assert font.bold is True

        # Weight just under 200 should not be bold
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="SemiBold",
            weight=199.9,
        )
        assert font.bold is False

    def test_italic_property_regular_style(self) -> None:
        """Test italic property returns False for regular style."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        assert font.italic is False

    def test_italic_property_italic_style(self) -> None:
        """Test italic property returns True for italic style."""
        font = FontInfo(
            postscript_name="Arial-ItalicMT",
            file="/path/to/arial-italic.ttf",
            family="Arial",
            style="Italic",
            weight=80.0,
        )
        assert font.italic is True

    def test_italic_property_case_insensitive(self) -> None:
        """Test italic property is case-insensitive."""
        for style in ["italic", "ITALIC", "Italic"]:
            font = FontInfo(
                postscript_name="Arial-ItalicMT",
                file="/path/to/arial-italic.ttf",
                family="Arial",
                style=style,
                weight=80.0,
            )
            assert font.italic is True

    def test_italic_property_oblique(self) -> None:
        """Test italic property returns True for oblique style."""
        font = FontInfo(
            postscript_name="Arial-Oblique",
            file="/path/to/arial-oblique.ttf",
            family="Arial",
            style="Oblique italic",
            weight=80.0,
        )
        assert font.italic is True


class TestFontInfoCSSWeight:
    """Tests for FontInfo CSS weight conversion methods."""

    def test_css_weight_property_regular(self) -> None:
        """Test css_weight property for regular weight."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        assert font.css_weight == 400

    def test_css_weight_property_bold(self) -> None:
        """Test css_weight property for bold weight."""
        font = FontInfo(
            postscript_name="Arial-BoldMT",
            file="/path/to/arial-bold.ttf",
            family="Arial",
            style="Bold",
            weight=200.0,
        )
        assert font.css_weight == 700

    def test_get_css_weight_numeric(self) -> None:
        """Test get_css_weight() returns numeric values by default."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        assert font.get_css_weight() == 400
        assert font.get_css_weight(semantic=False) == 400

    def test_get_css_weight_semantic_normal(self) -> None:
        """Test get_css_weight(semantic=True) returns 'normal' for 400."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        assert font.get_css_weight(semantic=True) == "normal"

    def test_get_css_weight_semantic_bold(self) -> None:
        """Test get_css_weight(semantic=True) returns 'bold' for 700."""
        font = FontInfo(
            postscript_name="Arial-BoldMT",
            file="/path/to/arial-bold.ttf",
            family="Arial",
            style="Bold",
            weight=200.0,
        )
        assert font.get_css_weight(semantic=True) == "bold"

    def test_get_css_weight_semantic_light(self) -> None:
        """Test get_css_weight(semantic=True) returns numeric for non-normal/bold."""
        font = FontInfo(
            postscript_name="Arial-Light",
            file="/path/to/arial-light.ttf",
            family="Arial",
            style="Light",
            weight=50.0,
        )
        # Light (300) has no semantic keyword in CSS
        assert font.get_css_weight(semantic=True) == 300

    def test_css_weight_all_ranges(self) -> None:
        """Test CSS weight mapping for all weight ranges."""
        test_cases = [
            (0, 100),  # thin
            (40, 200),  # extralight
            (50, 300),  # light
            (75, 350),  # semilight
            (80, 400),  # regular
            (100, 500),  # medium
            (180, 600),  # semibold
            (200, 700),  # bold
            (205, 800),  # extrabold
            (210, 900),  # black
        ]

        for fc_weight, expected_css in test_cases:
            font = FontInfo(
                postscript_name="TestFont",
                file="/path/to/test.ttf",
                family="Test",
                style="Test",
                weight=float(fc_weight),
            )
            assert font.css_weight == expected_css, (
                f"FC weight {fc_weight} should map to CSS {expected_css}"
            )


class TestFontInfoFind:
    """Tests for FontInfo.find static method."""

    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_success(self, mock_match: MagicMock) -> None:
        """Test find method with fontconfig fallback for font not in static mapping."""
        mock_match.return_value = {
            "file": "/path/to/custom.ttf",
            "family": "CustomFont",
            "style": "Regular",
            "weight": 80.0,
        }

        # Use a font name that's definitely not in the static mapping
        font = FontInfo.find("CustomFont-Regular")

        assert font is not None
        assert font.postscript_name == "CustomFont-Regular"
        assert font.file == "/path/to/custom.ttf"
        assert font.family == "CustomFont"
        assert font.style == "Regular"
        assert font.weight == 80.0

        mock_match.assert_called_once_with(
            pattern=":postscriptname=CustomFont-Regular",
            select=("file", "family", "style", "weight"),
        )

    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_static_mapping_priority(self, mock_match: MagicMock) -> None:
        """Test that static mapping is used first, fontconfig not called."""
        # ArialMT is in the static mapping, so fontconfig should NOT be called
        font = FontInfo.find("ArialMT")

        assert font is not None
        assert font.postscript_name == "ArialMT"
        assert font.family == "Arial"
        assert font.style == "Regular"
        assert font.weight == 80.0
        assert font.file == ""  # No file path from static mapping

        # Fontconfig should not have been called
        mock_match.assert_not_called()

    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_not_found(
        self, mock_match: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test find method when font is not found."""
        mock_match.return_value = None

        with caplog.at_level(logging.WARNING):
            font = FontInfo.find("NonExistentFont")

        assert font is None
        assert "Font 'NonExistentFont' not found" in caplog.text
        assert "Make sure the font is installed on your system" in caplog.text

    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_empty_result(
        self, mock_match: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test find method with empty match result."""
        mock_match.return_value = {}

        with caplog.at_level(logging.WARNING):
            font = FontInfo.find("EmptyFont")

        assert font is None
        assert "Font 'EmptyFont' not found" in caplog.text

    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_bold_font(self, mock_match: MagicMock) -> None:
        """Test find method for bold font via fontconfig fallback."""
        mock_match.return_value = {
            "file": "/path/to/custom-bold.ttf",
            "family": "CustomFont",
            "style": "Bold",
            "weight": 200.0,
        }

        font = FontInfo.find("CustomFont-Bold")

        assert font is not None
        assert font.bold is True
        assert font.italic is False

    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_italic_font(self, mock_match: MagicMock) -> None:
        """Test find method for italic font via fontconfig fallback."""
        mock_match.return_value = {
            "file": "/path/to/custom-italic.ttf",
            "family": "CustomFont",
            "style": "Italic",
            "weight": 80.0,
        }

        font = FontInfo.find("CustomFont-Italic")

        assert font is not None
        assert font.bold is False
        assert font.italic is True

    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_bold_italic_font(self, mock_match: MagicMock) -> None:
        """Test find method for bold italic font via fontconfig fallback."""
        mock_match.return_value = {
            "file": "/path/to/custom-bolditalic.ttf",
            "family": "CustomFont",
            "style": "Bold Italic",
            "weight": 200.0,
        }

        font = FontInfo.find("CustomFont-BoldItalic")

        assert font is not None
        assert font.bold is True
        assert font.italic is True

    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_with_special_characters(self, mock_match: MagicMock) -> None:
        """Test find method with postscript name containing special characters."""
        mock_match.return_value = {
            "file": "/path/to/font.ttf",
            "family": "Special Font",
            "style": "Regular",
            "weight": 80.0,
        }

        font = FontInfo.find("SpecialFont-Regular_1.0")

        assert font is not None
        assert font.postscript_name == "SpecialFont-Regular_1.0"
        mock_match.assert_called_once_with(
            pattern=":postscriptname=SpecialFont-Regular_1.0",
            select=("file", "family", "style", "weight"),
        )


class TestFontInfoSerialization:
    """Tests for FontInfo serialization methods."""

    def test_to_dict(self) -> None:
        """Test to_dict method converts FontInfo to dictionary."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        result = font.to_dict()

        assert isinstance(result, dict)
        assert result["postscript_name"] == "ArialMT"
        assert result["file"] == "/path/to/arial.ttf"
        assert result["family"] == "Arial"
        assert result["style"] == "Regular"
        assert result["weight"] == 80.0

    def test_from_dict(self) -> None:
        """Test from_dict classmethod creates FontInfo from dictionary."""
        data: dict[str, Any] = {
            "postscript_name": "ArialMT",
            "file": "/path/to/arial.ttf",
            "family": "Arial",
            "style": "Regular",
            "weight": 80.0,
        }

        font = FontInfo.from_dict(cast(dict[str, str | float], data))

        assert isinstance(font, FontInfo)
        assert font.postscript_name == "ArialMT"
        assert font.file == "/path/to/arial.ttf"
        assert font.family == "Arial"
        assert font.style == "Regular"
        assert font.weight == 80.0

    def test_to_dict_from_dict_roundtrip(self) -> None:
        """Test that to_dict and from_dict are symmetric."""
        original = FontInfo(
            postscript_name="Arial-BoldMT",
            file="/path/to/arial-bold.ttf",
            family="Arial",
            style="Bold",
            weight=200.0,
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = FontInfo.from_dict(data)

        # Verify all fields match
        assert restored.postscript_name == original.postscript_name
        assert restored.file == original.file
        assert restored.family == original.family
        assert restored.style == original.style
        assert restored.weight == original.weight

    def test_from_dict_with_string_weight(self) -> None:
        """Test from_dict handles string weight by converting to float."""
        data: dict[str, Any] = {
            "postscript_name": "ArialMT",
            "file": "/path/to/arial.ttf",
            "family": "Arial",
            "style": "Regular",
            "weight": "80.0",  # String instead of float
        }

        font = FontInfo.from_dict(cast(dict[str, str | float], data))

        assert font.weight == 80.0
        assert isinstance(font.weight, float)
