"""Tests for font_mapping module."""

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from psd2svg.core import font_mapping as fm
from psd2svg.core.font_utils import FontInfo


class TestFindInMapping:
    """Tests for find_in_mapping function."""

    def test_find_in_default_mapping(self) -> None:
        """Test finding a font in the default mapping."""
        result = fm.find_in_mapping("ArialMT")

        assert result is not None
        assert result["family"] == "Arial"
        assert result["style"] == "Regular"
        assert result["weight"] == 80.0

    def test_find_in_custom_mapping(self) -> None:
        """Test that custom mapping takes priority over default mapping."""
        custom_mapping = {
            "ArialMT": {"family": "CustomArial", "style": "Custom", "weight": 123.0}
        }

        result = fm.find_in_mapping("ArialMT", custom_mapping)

        assert result is not None
        assert result["family"] == "CustomArial"
        assert result["style"] == "Custom"
        assert result["weight"] == 123.0

    def test_find_not_found(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test when font is not found in any mapping."""
        with caplog.at_level(logging.DEBUG):
            result = fm.find_in_mapping("NonExistentFont-Regular")

        assert result is None
        assert "not found in any mapping" in caplog.text

    def test_find_with_empty_custom_mapping(self) -> None:
        """Test with empty custom mapping falls back to default."""
        result = fm.find_in_mapping("ArialMT", {})

        assert result is not None
        assert result["family"] == "Arial"

    def test_find_validates_font_data(self) -> None:
        """Test that invalid font data is rejected."""
        custom_mapping = {
            "BadFont": {"family": "Test"}  # Missing style and weight
        }

        result = fm.find_in_mapping("BadFont", custom_mapping)

        # Should return None because validation failed
        assert result is None

    def test_find_common_fonts(self) -> None:
        """Test that common fonts are in the default mapping."""
        common_fonts = [
            ("ArialMT", "Arial"),
            ("TimesNewRomanPSMT", "Times New Roman"),
            ("Helvetica", "Helvetica"),
            ("Courier", "Courier"),
            ("NotoSansCJKjp-Regular", "Noto Sans CJK JP"),
            ("MyriadPro-Regular", "Myriad Pro"),
        ]

        for postscript_name, expected_family in common_fonts:
            result = fm.find_in_mapping(postscript_name)
            assert result is not None, f"{postscript_name} not found in mapping"
            assert result["family"] == expected_family


class TestLoadFontMappingFromJSON:
    """Tests for load_font_mapping_from_json function."""

    def test_load_valid_json(self, tmp_path: Path) -> None:
        """Test loading a valid JSON file."""
        json_file = tmp_path / "fonts.json"
        mapping_data = {
            "TestFont-Regular": {
                "family": "Test Font",
                "style": "Regular",
                "weight": 80.0,
            },
            "TestFont-Bold": {"family": "Test Font", "style": "Bold", "weight": 200.0},
        }

        with open(json_file, "w") as f:
            json.dump(mapping_data, f)

        result = fm.load_font_mapping_from_json(json_file)

        assert len(result) == 2
        assert result["TestFont-Regular"]["family"] == "Test Font"
        assert result["TestFont-Bold"]["weight"] == 200.0

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Test loading a non-existent file."""
        json_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError, match="Font mapping file not found"):
            fm.load_font_mapping_from_json(json_file)

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Test loading a file with invalid JSON."""
        json_file = tmp_path / "invalid.json"

        with open(json_file, "w") as f:
            f.write("{invalid json")

        with pytest.raises(json.JSONDecodeError, match="Invalid JSON"):
            fm.load_font_mapping_from_json(json_file)

    def test_load_non_dict_json(self, tmp_path: Path) -> None:
        """Test loading JSON that's not a dictionary."""
        json_file = tmp_path / "array.json"

        with open(json_file, "w") as f:
            json.dump(["not", "a", "dict"], f)

        with pytest.raises(ValueError, match="Font mapping must be a dictionary"):
            fm.load_font_mapping_from_json(json_file)

    def test_load_empty_postscript_name(self, tmp_path: Path) -> None:
        """Test loading JSON with empty PostScript name."""
        json_file = tmp_path / "empty_name.json"

        # JSON requires string keys, but we can test empty string
        with open(json_file, "w") as f:
            json.dump({"": {"family": "Test", "style": "Regular", "weight": 80.0}}, f)

        # Empty string keys are technically valid in the JSON loader
        # but would be caught if strict validation is added later
        result = fm.load_font_mapping_from_json(json_file)
        assert "" in result  # Currently allowed

    def test_load_missing_required_fields(self, tmp_path: Path) -> None:
        """Test loading JSON with missing required fields."""
        json_file = tmp_path / "missing_fields.json"
        mapping_data = {
            "TestFont": {"family": "Test Font"}  # Missing style and weight
        }

        with open(json_file, "w") as f:
            json.dump(mapping_data, f)

        with pytest.raises(ValueError, match="missing required fields"):
            fm.load_font_mapping_from_json(json_file)

    def test_load_invalid_field_types(self, tmp_path: Path) -> None:
        """Test loading JSON with invalid field types."""
        json_file = tmp_path / "invalid_types.json"
        mapping_data = {
            "TestFont": {
                "family": 123,
                "style": "Regular",
                "weight": 80.0,
            }  # family should be string
        }

        with open(json_file, "w") as f:
            json.dump(mapping_data, f)

        with pytest.raises(ValueError, match="must be a string"):
            fm.load_font_mapping_from_json(json_file)

    def test_load_with_string_path(self, tmp_path: Path) -> None:
        """Test loading with string path (not Path object)."""
        json_file = tmp_path / "fonts.json"
        mapping_data = {
            "TestFont": {"family": "Test Font", "style": "Regular", "weight": 80.0}
        }

        with open(json_file, "w") as f:
            json.dump(mapping_data, f)

        result = fm.load_font_mapping_from_json(str(json_file))

        assert len(result) == 1
        assert result["TestFont"]["family"] == "Test Font"


class TestValidateFontData:
    """Tests for _validate_font_data function."""

    def test_validate_valid_data(self) -> None:
        """Test validating valid font data."""
        font_data = {"family": "Arial", "style": "Regular", "weight": 80.0}

        result = fm._validate_font_data(font_data, "ArialMT")

        assert result is not None
        assert result["family"] == "Arial"
        assert result["style"] == "Regular"
        assert result["weight"] == 80.0

    def test_validate_int_weight(self) -> None:
        """Test that integer weights are converted to float."""
        font_data = {"family": "Arial", "style": "Regular", "weight": 80}

        result = fm._validate_font_data(font_data, "ArialMT")

        assert result is not None
        assert result["weight"] == 80.0
        assert isinstance(result["weight"], float)

    def test_validate_non_dict(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test validating non-dictionary data."""
        with caplog.at_level(logging.WARNING):
            result = fm._validate_font_data("not a dict", "TestFont")  # type: ignore

        assert result is None
        assert "must be a dictionary" in caplog.text

    def test_validate_non_dict_raise_error(self) -> None:
        """Test validating non-dictionary data with raise_on_error=True."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            fm._validate_font_data("not a dict", "TestFont", raise_on_error=True)  # type: ignore

    def test_validate_missing_fields(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test validating data with missing fields."""
        font_data: dict[str, Any] = {"family": "Arial"}  # Missing style and weight

        with caplog.at_level(logging.WARNING):
            result = fm._validate_font_data(font_data, "TestFont")

        assert result is None
        assert "missing required fields" in caplog.text

    def test_validate_missing_fields_raise_error(self) -> None:
        """Test validating data with missing fields with raise_on_error=True."""
        font_data: dict[str, Any] = {"family": "Arial"}

        with pytest.raises(ValueError, match="missing required fields"):
            fm._validate_font_data(font_data, "TestFont", raise_on_error=True)

    def test_validate_invalid_family_type(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test validating data with non-string family."""
        font_data: dict[str, Any] = {"family": 123, "style": "Regular", "weight": 80.0}

        with caplog.at_level(logging.WARNING):
            result = fm._validate_font_data(font_data, "TestFont")

        assert result is None
        assert "Font family" in caplog.text
        assert "must be a string" in caplog.text

    def test_validate_invalid_style_type(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test validating data with non-string style."""
        font_data: dict[str, Any] = {"family": "Arial", "style": 123, "weight": 80.0}

        with caplog.at_level(logging.WARNING):
            result = fm._validate_font_data(font_data, "TestFont")

        assert result is None
        assert "Font style" in caplog.text
        assert "must be a string" in caplog.text

    def test_validate_invalid_weight_type(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test validating data with non-numeric weight."""
        font_data: dict[str, Any] = {
            "family": "Arial",
            "style": "Regular",
            "weight": "not a number",
        }

        with caplog.at_level(logging.WARNING):
            result = fm._validate_font_data(font_data, "TestFont")

        assert result is None
        assert "Font weight" in caplog.text
        assert "must be a number" in caplog.text


class TestDefaultFontMapping:
    """Tests for DEFAULT_FONT_MAPPING constant."""

    def test_default_mapping_exists(self) -> None:
        """Test that default mapping is loaded."""
        assert fm.DEFAULT_FONT_MAPPING is not None
        assert isinstance(fm.DEFAULT_FONT_MAPPING, dict)
        assert len(fm.DEFAULT_FONT_MAPPING) > 0

    def test_default_mapping_coverage(self) -> None:
        """Test that default mapping has reasonable coverage."""
        # Should have at least 500 fonts (we have 570+)
        assert len(fm.DEFAULT_FONT_MAPPING) >= 500

    def test_default_mapping_structure(self) -> None:
        """Test that all entries in default mapping have correct structure."""
        for postscript_name, font_data in fm.DEFAULT_FONT_MAPPING.items():
            # PostScript name is a string
            assert isinstance(postscript_name, str)
            assert len(postscript_name) > 0

            # Font data is a dictionary
            assert isinstance(font_data, dict)

            # Required fields exist
            assert "family" in font_data
            assert "style" in font_data
            assert "weight" in font_data

            # Field types are correct
            assert isinstance(font_data["family"], str)
            assert isinstance(font_data["style"], str)
            assert isinstance(font_data["weight"], (int, float))

            # Weight is in valid range
            assert 0 <= font_data["weight"] <= 250

    def test_default_mapping_common_families(self) -> None:
        """Test that default mapping includes common font families."""
        # Get all unique family names
        families = {data["family"] for data in fm.DEFAULT_FONT_MAPPING.values()}

        # Check for common families
        expected_families = {
            "Arial",
            "Times New Roman",
            "Helvetica",
            "Courier",
            "Noto Sans",
            "Noto Sans CJK JP",
            "Roboto",
            "Open Sans",
        }

        for family in expected_families:
            assert family in families, (
                f"Expected family '{family}' not found in mapping"
            )

    def test_default_mapping_cjk_coverage(self) -> None:
        """Test that default mapping has good CJK coverage."""
        families = {data["family"] for data in fm.DEFAULT_FONT_MAPPING.values()}

        # Should have Japanese fonts
        assert any("Noto Sans CJK JP" in f for f in families)
        assert any("Noto Serif CJK JP" in f for f in families)

        # Should have Korean fonts
        assert any("Noto Sans CJK KR" in f for f in families)

        # Should have Chinese fonts
        assert any("Noto Sans CJK SC" in f for f in families)
        assert any("Noto Sans CJK TC" in f for f in families)


class TestFontMappingIntegration:
    """Integration tests for font_mapping parameter in conversion."""

    def test_custom_mapping_in_find(self) -> None:
        """Test that FontInfo.find respects custom font mapping."""
        custom_mapping: dict[str, dict[str, str | float]] = {
            "CustomFont-Test": {
                "family": "My Custom Font",
                "style": "Test",
                "weight": 150.0,
            }
        }

        # Font not in default mapping, but in custom mapping
        font_info = FontInfo.find("CustomFont-Test", font_mapping=custom_mapping)

        assert font_info is not None
        assert font_info.family == "My Custom Font"
        assert font_info.style == "Test"
        assert font_info.weight == 150.0
        assert font_info.file == ""  # No file path from mapping

    def test_custom_mapping_overrides_default(self) -> None:
        """Test that custom mapping overrides default for same PostScript name."""
        custom_mapping: dict[str, dict[str, str | float]] = {
            "ArialMT": {"family": "My Custom Arial", "style": "Custom", "weight": 999.0}
        }

        font_info = FontInfo.find("ArialMT", font_mapping=custom_mapping)

        assert font_info is not None
        assert font_info.family == "My Custom Arial"  # Custom, not "Arial"
        assert font_info.style == "Custom"
        assert font_info.weight == 999.0

    def test_font_mapping_with_none(self) -> None:
        """Test that None custom mapping works (uses default only)."""
        from psd2svg.core.font_utils import FontInfo

        font_info = FontInfo.find("ArialMT", font_mapping=None)

        assert font_info is not None
        assert font_info.family == "Arial"  # From default mapping


class TestSuffixParsing:
    """Tests for PostScript name suffix parsing fallback."""

    def test_parse_hyphenated_bold(self) -> None:
        """Test suffix parsing for hyphenated Bold variant."""
        font = FontInfo.lookup_static("CustomFont-Bold")

        assert font is not None
        assert font.family == "Custom Font"
        assert font.style == "Bold"
        assert font.weight == 200.0
        assert font.file == ""
        assert font.postscript_name == "CustomFont-Bold"

    def test_parse_hyphenated_italic(self) -> None:
        """Test suffix parsing for hyphenated Italic variant."""
        font = FontInfo.lookup_static("CustomFont-Italic")

        assert font is not None
        assert font.family == "Custom Font"
        assert font.style == "Italic"
        assert font.weight == 80.0
        assert font.italic is True

    def test_parse_compound_bold_italic(self) -> None:
        """Test suffix parsing for BoldItalic combined."""
        font = FontInfo.lookup_static("MyFont-BoldItalic")

        assert font is not None
        assert font.family == "My Font"
        assert font.style == "Bold Italic"
        assert font.weight == 200.0
        assert font.bold is True
        assert font.italic is True

    def test_parse_compound_light_italic(self) -> None:
        """Test suffix parsing for LightItalic combined."""
        font = FontInfo.lookup_static("TestFont-LightItalic")

        assert font is not None
        assert font.style == "Light Italic"
        assert font.weight == 50.0
        assert font.italic is True

    def test_parse_japanese_w6(self) -> None:
        """Test suffix parsing for Japanese W6 notation."""
        font = FontInfo.lookup_static("CustomFont-W6")

        assert font is not None
        assert font.weight == 180.0
        assert font.style == "W6"

    def test_parse_japanese_w0_to_w9(self) -> None:
        """Test suffix parsing for all Japanese W0-W9 notations."""
        test_cases = [
            ("Font-W0", 0.0, "W0"),
            ("Font-W1", 40.0, "W1"),
            ("Font-W2", 45.0, "W2"),
            ("Font-W3", 50.0, "W3"),
            ("Font-W4", 80.0, "W4"),
            ("Font-W5", 100.0, "W5"),
            ("Font-W6", 180.0, "W6"),
            ("Font-W7", 200.0, "W7"),
            ("Font-W8", 205.0, "W8"),
            ("Font-W9", 210.0, "W9"),
        ]

        for name, expected_weight, expected_style in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.weight == expected_weight
            assert font.style == expected_style

    def test_parse_camelcase_bold(self) -> None:
        """Test suffix parsing for camelCase Bold variant."""
        font = FontInfo.lookup_static("RobotoBold")

        assert font is not None
        assert font.family == "Roboto"
        assert font.style == "Bold"
        assert font.weight == 200.0

    def test_parse_camelcase_medium(self) -> None:
        """Test suffix parsing for camelCase Medium variant."""
        font = FontInfo.lookup_static("CustomMedium")

        assert font is not None
        assert font.family == "Custom"
        assert font.style == "Medium"
        assert font.weight == 100.0

    def test_parse_various_weights(self) -> None:
        """Test suffix parsing for various weight values."""
        test_cases = [
            ("Font-Thin", 0.0, "Thin"),
            ("Font-ExtraLight", 40.0, "ExtraLight"),
            ("Font-Light", 50.0, "Light"),
            ("Font-Regular", 80.0, "Regular"),
            ("Font-Medium", 100.0, "Medium"),
            ("Font-SemiBold", 180.0, "SemiBold"),
            ("Font-Bold", 200.0, "Bold"),
            ("Font-ExtraBold", 205.0, "ExtraBold"),
            ("Font-Black", 210.0, "Black"),
            ("Font-Heavy", 210.0, "Heavy"),
        ]

        for name, expected_weight, expected_style in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.weight == expected_weight
            assert font.style == expected_style

    def test_parse_family_name_cleaning(self) -> None:
        """Test that CamelCase family names are properly spaced."""
        test_cases = [
            ("OpenSans-Bold", "Open Sans"),
            ("NotoSansJP-Bold", "Noto Sans JP"),
            ("HelveticaNeue-Bold", "Helvetica Neue"),
            ("TimesNewRoman-Bold", "Times New Roman"),
        ]

        for ps_name, expected_family in test_cases:
            font = FontInfo.lookup_static(ps_name)
            assert font is not None, f"Failed to parse {ps_name}"
            assert font.family == expected_family

    def test_parse_multiple_hyphens(self) -> None:
        """Test suffix parsing with multiple hyphens (uses rsplit)."""
        font = FontInfo.lookup_static("Font-Name-With-Hyphens-Bold")

        assert font is not None
        assert font.family == "Font-Name-With-Hyphens"
        assert font.style == "Bold"
        assert font.weight == 200.0

    def test_unknown_suffix_returns_none(self) -> None:
        """Test that unrecognized suffix returns None."""
        font = FontInfo.lookup_static("MyFont-SuperCustomSuffix")
        assert font is None

    def test_numeric_suffix_returns_none(self) -> None:
        """Test that numeric suffix returns None."""
        font = FontInfo.lookup_static("Font-123")
        assert font is None

    def test_empty_suffix_returns_none(self) -> None:
        """Test that empty suffix returns None."""
        font = FontInfo.lookup_static("Font-")
        assert font is None

    def test_very_short_base_name_rejected(self) -> None:
        """Test that very short base names are rejected in camelCase parsing."""
        # AB-Bold should parse via hyphenated (Phase 1)
        font1 = FontInfo.lookup_static("AB-Bold")
        assert font1 is not None  # Hyphenated allows any length

        # ABBold should be rejected in camelCase (Phase 2)
        font2 = FontInfo.lookup_static("ABBold")
        assert font2 is None  # Base "AB" too short (< 3 chars)

    def test_static_mapping_takes_precedence(self) -> None:
        """Test that static mapping takes precedence over suffix parsing."""
        # ArialMT is in static mapping
        font = FontInfo.lookup_static("ArialMT")

        assert font is not None
        assert font.family == "Arial"  # From static mapping
        assert font.style == "Regular"  # From static mapping, not parsed from "MT"

    def test_custom_mapping_takes_precedence(self) -> None:
        """Test that custom mapping takes precedence over suffix parsing."""
        custom_mapping: dict[str, dict[str, str | float]] = {
            "CustomFont-Bold": {
                "family": "Override Family",
                "style": "Override Style",
                "weight": 999.0,
            }
        }

        font = FontInfo.lookup_static("CustomFont-Bold", font_mapping=custom_mapping)

        assert font is not None
        assert font.family == "Override Family"  # From custom mapping
        assert font.weight == 999.0  # Not 200.0 from suffix parsing

    def test_parse_oblique_variants(self) -> None:
        """Test suffix parsing for Oblique style variants."""
        test_cases = [
            ("Font-BoldOblique", "Bold Oblique", 200.0),
            ("Font-SemiBoldOblique", "SemiBold Oblique", 180.0),
            ("Font-ExtraBoldOblique", "ExtraBold Oblique", 205.0),
        ]

        for name, expected_style, expected_weight in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.style == expected_style
            assert font.weight == expected_weight

    def test_parse_alternative_spellings(self) -> None:
        """Test suffix parsing for alternative spellings."""
        # Semibold vs SemiBold
        font1 = FontInfo.lookup_static("Font-Semibold")
        font2 = FontInfo.lookup_static("Font-SemiBold")

        assert font1 is not None
        assert font2 is not None
        assert font1.style == "SemiBold"  # Normalized
        assert font2.style == "SemiBold"
        assert font1.weight == font2.weight == 180.0

        # Extrabold vs ExtraBold
        font3 = FontInfo.lookup_static("Font-Extrabold")
        font4 = FontInfo.lookup_static("Font-ExtraBold")

        assert font3 is not None
        assert font4 is not None
        assert font3.style == "ExtraBold"  # Normalized
        assert font4.style == "ExtraBold"
        assert font3.weight == font4.weight == 205.0

    def test_parse_roman_suffix(self) -> None:
        """Test suffix parsing for Roman style (Times-Roman pattern)."""
        font = FontInfo.lookup_static("CustomTimes-Roman")

        assert font is not None
        assert font.family == "Custom Times"
        assert font.style == "Roman"
        assert font.weight == 80.0

    def test_parse_mt_suffix(self) -> None:
        """Test suffix parsing for MT (Mac Type) suffix."""
        font = FontInfo.lookup_static("CustomFont-MT")

        assert font is not None
        assert font.family == "Custom Font"
        assert font.style == "Regular"  # MT maps to Regular
        assert font.weight == 80.0

    def test_no_false_positive_on_ambiguous_names(self) -> None:
        """Test that ambiguous font names don't cause false positives."""
        # "MyBoldIdea" should not be parsed as "MyBold" + "Idea" suffix
        # "Idea" is not a recognized suffix, should return None
        font = FontInfo.lookup_static("MyBoldIdea")
        assert font is None

        # "CompanyMedium" should not be parsed as "Company" + "Medium"
        # Actually, it SHOULD be parsed because "Medium" is a valid suffix
        # and the base "Company" is valid (>= 3 chars, starts uppercase)
        font2 = FontInfo.lookup_static("CompanyMedium")
        assert font2 is not None
        assert font2.family == "Company"
        assert font2.style == "Medium"

    def test_unicode_font_names(self) -> None:
        """Test suffix parsing with Unicode characters in base name."""
        font = FontInfo.lookup_static("日本語Font-Bold")

        assert font is not None
        assert font.family == "日本語Font"
        assert font.style == "Bold"
        assert font.weight == 200.0

    def test_css_weight_from_parsed_font(self) -> None:
        """Test that CSS weight is correctly derived from parsed fonts."""
        font = FontInfo.lookup_static("Custom-Bold")

        assert font is not None
        assert font.get_css_weight() == 700  # Bold = 700 in CSS

    def test_parse_abbreviated_suffixes(self) -> None:
        """Test suffix parsing for abbreviated suffixes (B, DB, EB, UB)."""
        test_cases = [
            ("RodinCattleyaPro-B", "Bold", 200.0),
            ("RodinCattleyaPro-DB", "SemiBold", 180.0),  # DemiBold
            ("RodinCattleyaPro-EB", "ExtraBold", 205.0),
            ("RodinCattleyaPro-UB", "Ultra", 210.0),  # UltraBold
            ("RowdyStd-EB", "ExtraBold", 205.0),
        ]

        for name, expected_style, expected_weight in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.style == expected_style
            assert font.weight == expected_weight

    def test_abbreviated_suffixes_not_in_camelcase(self) -> None:
        """Test that abbreviated suffixes don't cause false positives in camelCase."""
        # These should NOT be parsed because abbreviated suffixes
        # are not in SAFE_CAMELCASE_SUFFIXES to avoid false positives
        test_cases = [
            "WebDB",  # Not "Web" + "DB"
            "TestEB",  # Not "Test" + "EB"
            "CompanyB",  # Not "Company" + "B"
        ]

        for name in test_cases:
            font = FontInfo.lookup_static(name)
            # Should return None because abbreviated suffixes excluded from camelCase
            assert font is None, f"{name} should not be parsed"

    def test_parse_demibold_ultrabold_full_names(self) -> None:
        """Test parsing of full DemiBold and UltraBold names."""
        test_cases = [
            ("CustomFont-DemiBold", "SemiBold", 180.0),
            ("CustomFont-UltraBold", "Ultra", 210.0),
        ]

        for name, expected_style, expected_weight in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.style == expected_style
            assert font.weight == expected_weight

    def test_parse_lowercase_suffixes(self) -> None:
        """Test case-insensitive suffix parsing for lowercase variants."""
        test_cases = [
            ("mplus-1c-bold", "mplus-1c", "Bold", 200.0),
            ("mplus-1c-medium", "mplus-1c", "Medium", 100.0),
            ("mplus-2c-heavy", "mplus-2c", "Heavy", 210.0),
            ("rounded-x-mplus-1c-light", "rounded-x-mplus-1c", "Light", 50.0),
            ("CustomFont-italic", "Custom Font", "Italic", 80.0),
            ("TestFont-regular", "Test Font", "Regular", 80.0),
        ]

        for name, expected_family, expected_style, expected_weight in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.family == expected_family
            assert font.style == expected_style
            assert font.weight == expected_weight

    def test_parse_uppercase_suffixes(self) -> None:
        """Test case-insensitive suffix parsing for uppercase variants."""
        test_cases = [
            ("Font-BOLD", "Bold", 200.0),
            ("Font-MEDIUM", "Medium", 100.0),
            ("Font-LIGHT", "Light", 50.0),
        ]

        for name, expected_style, expected_weight in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.style == expected_style
            assert font.weight == expected_weight

    def test_parse_japanese_w_case_insensitive(self) -> None:
        """Test Japanese W-notation is case-insensitive."""
        test_cases = [
            ("Font-w6", "W6", 180.0),
            ("Font-W6", "W6", 180.0),
            ("Font-w3", "W3", 50.0),
            ("Font-W9", "W9", 210.0),
        ]

        for name, expected_style, expected_weight in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.style == expected_style
            assert font.weight == expected_weight

    def test_parse_mixed_case_suffixes(self) -> None:
        """Test suffix parsing handles mixed case gracefully."""
        test_cases = [
            ("Font-bOlD", "Bold", 200.0),
            ("Font-MeDiUm", "Medium", 100.0),
        ]

        for name, expected_style, expected_weight in test_cases:
            font = FontInfo.lookup_static(name)
            assert font is not None, f"Failed to parse {name}"
            assert font.style == expected_style
            assert font.weight == expected_weight
