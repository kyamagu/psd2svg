"""Tests for font_mapping module."""

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from psd2svg.core import font_mapping as fm


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
        from psd2svg.core.font_utils import FontInfo

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
        from psd2svg.core.font_utils import FontInfo

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
