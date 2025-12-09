"""Tests for psd2svg.core.font_utils module."""

import logging
import sys
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from psd2svg.core.font_utils import FontInfo, HAS_FONTCONFIG, create_file_url


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

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
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
        # Must use disable_static_mapping=True to enable platform fallback
        font = FontInfo.find("CustomFont-Regular", disable_static_mapping=True)

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

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
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

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_not_found(
        self, mock_match: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test find method when font is not found."""
        mock_match.return_value = None

        with caplog.at_level(logging.WARNING):
            font = FontInfo.find("NonExistentFont", disable_static_mapping=True)

        assert font is None
        assert "Font 'NonExistentFont' not found" in caplog.text
        assert "Make sure the font is installed on your system" in caplog.text

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_empty_result(
        self, mock_match: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test find method with empty match result."""
        mock_match.return_value = {}

        with caplog.at_level(logging.WARNING):
            font = FontInfo.find("EmptyFont", disable_static_mapping=True)

        assert font is None
        assert "Font 'EmptyFont' not found" in caplog.text

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_bold_font(self, mock_match: MagicMock) -> None:
        """Test find method for bold font via fontconfig fallback."""
        mock_match.return_value = {
            "file": "/path/to/custom-bold.ttf",
            "family": "CustomFont",
            "style": "Bold",
            "weight": 200.0,
        }

        font = FontInfo.find("CustomFont-Bold", disable_static_mapping=True)

        assert font is not None
        assert font.bold is True
        assert font.italic is False

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_italic_font(self, mock_match: MagicMock) -> None:
        """Test find method for italic font via fontconfig fallback."""
        mock_match.return_value = {
            "file": "/path/to/custom-italic.ttf",
            "family": "CustomFont",
            "style": "Italic",
            "weight": 80.0,
        }

        font = FontInfo.find("CustomFont-Italic", disable_static_mapping=True)

        assert font is not None
        assert font.bold is False
        assert font.italic is True

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_bold_italic_font(self, mock_match: MagicMock) -> None:
        """Test find method for bold italic font via fontconfig fallback."""
        mock_match.return_value = {
            "file": "/path/to/custom-bolditalic.ttf",
            "family": "CustomFont",
            "style": "Bold Italic",
            "weight": 200.0,
        }

        font = FontInfo.find("CustomFont-BoldItalic", disable_static_mapping=True)

        assert font is not None
        assert font.bold is True
        assert font.italic is True

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_with_special_characters(self, mock_match: MagicMock) -> None:
        """Test find method with postscript name containing special characters."""
        mock_match.return_value = {
            "file": "/path/to/font.ttf",
            "family": "Special Font",
            "style": "Regular",
            "weight": 80.0,
        }

        font = FontInfo.find("SpecialFont-Regular_1.0", disable_static_mapping=True)

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


class TestFontInfoResolve:
    """Tests for FontInfo.resolve() method."""

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig")
    def test_resolve_exact_match_no_substitution(self, mock_fc: MagicMock) -> None:
        """Test resolve() when font is found with exact match (no substitution)."""
        mock_fc.match.return_value = {
            "file": "/usr/share/fonts/truetype/arial.ttf",
            "family": "Arial",
            "style": "Regular",
            "weight": 80.0,
        }

        font = FontInfo(
            postscript_name="ArialMT",
            file="",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        resolved = font.resolve()

        assert resolved is not None
        assert resolved.postscript_name == "ArialMT"
        assert resolved.file == "/usr/share/fonts/truetype/arial.ttf"
        assert resolved.family == "Arial"
        assert resolved.style == "Regular"
        assert resolved.weight == 80.0

        # Original should be unchanged (immutable)
        assert font.file == ""

        # Called with correct pattern
        mock_fc.match.assert_called_once_with(
            pattern=":postscriptname=ArialMT",
            select=("file", "family", "style", "weight"),
        )

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig")
    def test_resolve_with_substitution(
        self, mock_fc: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test resolve() when font is substituted (different family)."""
        mock_fc.match.return_value = {
            "file": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "family": "DejaVu Sans",
            "style": "Regular",
            "weight": 80.0,
        }

        font = FontInfo(
            postscript_name="HelveticaMT",
            file="",
            family="Helvetica",
            style="Regular",
            weight=80.0,
        )

        with caplog.at_level(logging.INFO):
            resolved = font.resolve()

        assert resolved is not None
        assert resolved.postscript_name == "HelveticaMT"
        assert resolved.file == "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        assert resolved.family == "DejaVu Sans"  # Different from original!
        assert resolved.style == "Regular"
        assert resolved.weight == 80.0

        # Should log substitution
        assert "Font substitution" in caplog.text
        assert "Helvetica" in caplog.text
        assert "DejaVu Sans" in caplog.text

        # Original unchanged
        assert font.family == "Helvetica"
        assert font.file == ""

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig")
    def test_resolve_font_not_found(self, mock_fc: MagicMock) -> None:
        """Test resolve() when font is not found."""
        mock_fc.match.return_value = None

        font = FontInfo(
            postscript_name="UnknownFont",
            file="",
            family="Unknown",
            style="Regular",
            weight=80.0,
        )

        resolved = font.resolve()

        assert resolved is None
        # Original unchanged
        assert font.family == "Unknown"

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig")
    def test_resolve_font_no_file_in_result(self, mock_fc: MagicMock) -> None:
        """Test resolve() when fontconfig returns result without file."""
        mock_fc.match.return_value = {
            "family": "Arial",
            "style": "Regular",
            "weight": 80.0,
            # Missing "file" key
        }

        font = FontInfo(
            postscript_name="ArialMT",
            file="",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        resolved = font.resolve()

        assert resolved is None

    @patch("psd2svg.core.font_utils.HAS_WINDOWS_FONTS", False)
    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", False)
    def test_resolve_no_fontconfig_available(self) -> None:
        """Test resolve() when neither fontconfig nor Windows fonts are available."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        resolved = font.resolve()

        assert resolved is None
        # Original unchanged
        assert font.family == "Arial"

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig")
    def test_resolve_handles_exception(
        self, mock_fc: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test resolve() handles fontconfig exceptions gracefully."""
        mock_fc.match.side_effect = Exception("Fontconfig error")

        font = FontInfo(
            postscript_name="ArialMT",
            file="",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        with caplog.at_level(logging.WARNING):
            resolved = font.resolve()

        assert resolved is None
        assert "Font resolution failed" in caplog.text
        assert "ArialMT" in caplog.text

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig")
    def test_resolve_immutability(self, mock_fc: MagicMock) -> None:
        """Test that resolve() doesn't modify the original FontInfo."""
        mock_fc.match.return_value = {
            "file": "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "family": "DejaVu Sans",
            "style": "Regular",
            "weight": 80.0,
        }

        original = FontInfo(
            postscript_name="ArialMT",
            file="",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        # Store original values
        orig_file = original.file
        orig_family = original.family

        # Resolve
        resolved = original.resolve()

        # Original should be completely unchanged
        assert original.file == orig_file
        assert original.family == orig_family
        assert resolved is not original  # Different object

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @patch("psd2svg.core.font_utils.os.path.exists")
    def test_resolve_with_existing_file_path(self, mock_exists: MagicMock) -> None:
        """Test that resolve() returns self when font already has valid file path."""
        mock_exists.return_value = True

        font_info = FontInfo(
            postscript_name="ArialMT",
            file="/usr/share/fonts/truetype/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        # Should return self without querying fontconfig
        resolved = font_info.resolve()

        # Should return the same instance (self)
        assert resolved is font_info
        assert resolved.file == "/usr/share/fonts/truetype/arial.ttf"

        # Verify os.path.exists was called
        mock_exists.assert_called_once_with("/usr/share/fonts/truetype/arial.ttf")

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @patch("psd2svg.core.font_utils.os.path.exists")
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig")
    def test_resolve_with_invalid_file_path(
        self, mock_fc: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test that resolve() queries fontconfig when file path is invalid."""
        mock_exists.return_value = False  # File doesn't exist
        mock_fc.match.return_value = {
            "file": "/usr/share/fonts/truetype/dejavu.ttf",
            "family": "DejaVu Sans",
            "style": "Book",
            "weight": 80.0,
        }

        font_info = FontInfo(
            postscript_name="ArialMT",
            file="/invalid/path/arial.ttf",  # Invalid path
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        # Should query fontconfig because file path is invalid
        resolved = font_info.resolve()

        # Should get resolved font from fontconfig
        assert resolved is not None
        assert resolved.file == "/usr/share/fonts/truetype/dejavu.ttf"
        assert resolved.family == "DejaVu Sans"

        # Verify both checks were made
        mock_exists.assert_called_once_with("/invalid/path/arial.ttf")
        mock_fc.match.assert_called_once()


class TestFontInfoIsResolved:
    """Test FontInfo.is_resolved() method."""

    @patch("os.path.exists")
    def test_is_resolved_with_valid_file(self, mock_exists: MagicMock) -> None:
        """Test is_resolved() returns True when font has valid file path."""
        mock_exists.return_value = True

        font_info = FontInfo(
            postscript_name="ArialMT",
            file="/usr/share/fonts/truetype/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        assert font_info.is_resolved() is True
        mock_exists.assert_called_once_with("/usr/share/fonts/truetype/arial.ttf")

    def test_is_resolved_with_no_file(self) -> None:
        """Test is_resolved() returns False when font has no file path."""
        font_info = FontInfo(
            postscript_name="ArialMT",
            file="",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        assert font_info.is_resolved() is False

    def test_is_resolved_with_empty_string_file(self) -> None:
        """Test is_resolved() returns False when font file is empty string."""
        # Note: FontInfo.file is typed as str, not str | None, so we test empty string
        font_info = FontInfo(
            postscript_name="ArialMT",
            file="",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        assert font_info.is_resolved() is False

    @patch("os.path.exists")
    def test_is_resolved_with_nonexistent_file(self, mock_exists: MagicMock) -> None:
        """Test is_resolved() returns False when file path doesn't exist."""
        mock_exists.return_value = False

        font_info = FontInfo(
            postscript_name="ArialMT",
            file="/nonexistent/path/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        assert font_info.is_resolved() is False
        mock_exists.assert_called_once_with("/nonexistent/path/arial.ttf")

    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", False)
    @patch("psd2svg.core.font_utils.HAS_WINDOWS_FONTS", False)
    @patch("os.path.exists")
    def test_is_resolved_from_static_mapping(self, mock_exists: MagicMock) -> None:
        """Test is_resolved() returns False for font from static mapping (no file)."""
        # Static mapping doesn't provide file paths
        # Mock platform-specific resolution as unavailable to force static mapping
        font_info = FontInfo.find("ArialMT")

        assert font_info is not None
        assert font_info.file == ""
        assert font_info.is_resolved() is False

        # Should not call os.path.exists for empty string
        mock_exists.assert_not_called()

    @patch("os.path.exists")
    @patch("psd2svg.core.font_utils.HAS_FONTCONFIG", True)
    @patch("psd2svg.core.font_utils.HAS_WINDOWS_FONTS", False)
    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig")
    def test_is_resolved_after_resolve(
        self, mock_fc: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test is_resolved() returns True after successful resolve()."""
        mock_exists.return_value = True
        mock_fc.match.return_value = {
            "file": "/usr/share/fonts/truetype/dejavu.ttf",
            "family": "DejaVu Sans",
            "style": "Book",
            "weight": 80.0,
        }

        # Start with unresolved font from static mapping
        with patch("psd2svg.core.font_utils.HAS_FONTCONFIG", False):
            font_info = FontInfo.find("ArialMT")
        assert font_info is not None
        assert font_info.is_resolved() is False

        # Resolve to system font
        resolved = font_info.resolve()
        assert resolved is not None
        assert resolved.is_resolved() is True


class TestCreateFileUrl:
    """Tests for create_file_url() function."""

    def test_create_file_url_unix(self, tmp_path: Path) -> None:
        """Test file URL creation on Linux/macOS."""
        font_file = tmp_path / "test.ttf"
        font_file.write_bytes(b"FAKE")

        url = create_file_url(str(font_file))

        # Should be file:// + absolute path
        assert url.startswith("file:///")
        assert Path(font_file).as_posix() in url

    def test_create_file_url_with_spaces(self, tmp_path: Path) -> None:
        """Test file URL with spaces in path."""
        font_dir = tmp_path / "My Fonts"
        font_dir.mkdir()
        font_file = font_dir / "Test Font.ttf"
        font_file.write_bytes(b"FAKE")

        url = create_file_url(str(font_file))

        # Spaces should be encoded as %20
        assert "My%20Fonts" in url
        assert "Test%20Font" in url
        assert " " not in url  # No literal spaces

    def test_create_file_url_with_unicode(self, tmp_path: Path) -> None:
        """Test file URL with non-ASCII characters."""
        font_dir = tmp_path / "日本語"
        font_dir.mkdir()
        font_file = font_dir / "font.ttf"
        font_file.write_bytes(b"FAKE")

        url = create_file_url(str(font_file))

        # Unicode should be percent-encoded
        assert url.startswith("file:///")
        assert "%" in url  # Has encoded characters

    def test_create_file_url_nonexistent(self, tmp_path: Path) -> None:
        """Test error handling for nonexistent file."""
        nonexistent = tmp_path / "missing.ttf"

        with pytest.raises(FileNotFoundError, match="Font file not found"):
            create_file_url(str(nonexistent))

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_create_file_url_windows(self, tmp_path: Path) -> None:
        """Test file URL creation on Windows."""
        font_file = tmp_path / "test.ttf"
        font_file.write_bytes(b"FAKE")

        url = create_file_url(str(font_file))

        # Should be file:///C:/... format
        assert url.startswith("file:///")
        assert ":" in url  # Drive letter
        assert "\\" not in url  # No backslashes


class TestFontInfoFindWithCharset:
    """Tests for FontInfo.find() with charset_codepoints parameter."""

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    @patch("psd2svg.core.font_utils.fontconfig.CharSet")
    def test_find_with_charset_not_in_static_mapping(
        self, mock_charset_class: MagicMock, mock_match: MagicMock
    ) -> None:
        """Test find with charset for font not in static mapping."""
        # Mock CharSet creation
        mock_charset_instance = MagicMock()
        mock_charset_class.from_codepoints.return_value = mock_charset_instance

        # Mock fontconfig match result
        mock_match.return_value = {
            "file": "/path/to/noto-sans-cjk.ttf",
            "family": "Noto Sans CJK JP",
            "style": "Regular",
            "weight": 80.0,
        }

        # Test with charset codepoints (Japanese hiragana)
        # Use a font name NOT in static mapping
        codepoints = {0x3042, 0x3044, 0x3046}
        font = FontInfo.find(
            "MyCustomCJKFont-Regular",
            charset_codepoints=codepoints,
            disable_static_mapping=True,
        )

        assert font is not None
        assert font.postscript_name == "MyCustomCJKFont-Regular"
        assert font.file == "/path/to/noto-sans-cjk.ttf"
        assert font.family == "Noto Sans CJK JP"

        # Verify CharSet was created with sorted codepoints
        mock_charset_class.from_codepoints.assert_called_once_with(sorted(codepoints))

        # Verify fontconfig.match was called with properties dict including charset
        mock_match.assert_called_once()
        call_kwargs = mock_match.call_args.kwargs
        assert "properties" in call_kwargs
        assert call_kwargs["properties"]["postscriptname"] == "MyCustomCJKFont-Regular"
        assert call_kwargs["properties"]["charset"] == mock_charset_instance

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_with_charset_in_static_mapping(self, mock_match: MagicMock) -> None:
        """Test find with charset for font in static mapping (charset ignored)."""
        codepoints = {0x3042, 0x3044, 0x3046}

        # ArialMT is in static mapping, should return immediately without charset matching
        font = FontInfo.find("ArialMT", charset_codepoints=codepoints)

        assert font is not None
        assert font.postscript_name == "ArialMT"
        assert font.family == "Arial"
        assert font.file == ""  # No file path from static mapping

        # fontconfig.match should NOT be called (static mapping takes priority)
        mock_match.assert_not_called()

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    @patch("psd2svg.core.font_utils.fontconfig.CharSet")
    def test_find_charset_matching_falls_back_on_error(
        self,
        mock_charset_class: MagicMock,
        mock_match: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test graceful fallback when charset matching fails."""
        # Mock CharSet to raise exception
        mock_charset_class.from_codepoints.side_effect = Exception(
            "CharSet creation failed"
        )

        # Fallback call succeeds
        mock_match.return_value = {
            "file": "/path/to/font.ttf",
            "family": "SomeFont",
            "style": "Regular",
            "weight": 80.0,
        }

        codepoints = {0x3042, 0x3044}

        with caplog.at_level(logging.WARNING):
            font = FontInfo.find(
                "CustomFont", charset_codepoints=codepoints, disable_static_mapping=True
            )

        # Should still succeed via fallback
        assert font is not None
        assert font.family == "SomeFont"

        # Check warning was logged
        assert any(
            "Charset-based matching failed" in record.message
            and "Falling back to name-only matching" in record.message
            for record in caplog.records
        )

        # Verify fallback to name-only matching was attempted
        assert mock_match.call_count == 1
        call_kwargs = mock_match.call_args.kwargs
        assert "pattern" in call_kwargs
        assert call_kwargs["pattern"] == ":postscriptname=CustomFont"

    @pytest.mark.skipif(not HAS_FONTCONFIG, reason="Requires fontconfig (Linux/macOS)")
    @patch("psd2svg.core.font_utils.fontconfig.match")
    def test_find_without_charset_uses_name_only(self, mock_match: MagicMock) -> None:
        """Test find without charset parameter uses name-only matching."""
        mock_match.return_value = {
            "file": "/path/to/font.ttf",
            "family": "CustomFont",
            "style": "Regular",
            "weight": 80.0,
        }

        # No charset_codepoints parameter
        font = FontInfo.find("CustomFont-Regular", disable_static_mapping=True)

        assert font is not None

        # Verify name-only matching was used
        mock_match.assert_called_once_with(
            pattern=":postscriptname=CustomFont-Regular",
            select=("file", "family", "style", "weight"),
        )
