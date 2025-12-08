"""Tests for generate_font_mapping CLI tool."""

import json
import sys
from pathlib import Path

import pytest

from psd2svg.tools import generate_font_mapping as gfm


class TestExtractFontsFromPSD:
    """Tests for extract_fonts_from_psd function."""

    def test_extract_from_type_layer(self) -> None:
        """Test extracting fonts from a PSD with text layers."""
        psd_path = Path("tests/fixtures/layer-types/type-layer.psd")
        fonts = gfm.extract_fonts_from_psd(psd_path)

        # Should find fonts used in visible text layers
        assert len(fonts) > 0
        assert isinstance(fonts, set)

        # Check for specific fonts we know are in the visible text layers
        assert "ArialMT" in fonts

    def test_extract_from_nonexistent_file(self) -> None:
        """Test that nonexistent file raises exception."""
        psd_path = Path("nonexistent.psd")

        with pytest.raises(Exception, match="Failed to open PSD file"):
            gfm.extract_fonts_from_psd(psd_path)

    def test_extract_returns_unique_fonts(self) -> None:
        """Test that duplicate font names are deduplicated."""
        psd_path = Path("tests/fixtures/layer-types/type-layer.psd")
        fonts = gfm.extract_fonts_from_psd(psd_path)

        # Should return a set (no duplicates)
        assert isinstance(fonts, set)


class TestGenerateMapping:
    """Tests for generate_mapping function."""

    def test_generate_from_single_psd(self) -> None:
        """Test generating mapping from a single PSD file."""
        psd_files = [Path("tests/fixtures/layer-types/type-layer.psd")]
        mapping = gfm.generate_mapping(psd_files, verbose=False)

        # Should generate mapping for all fonts in visible layers
        assert len(mapping) > 0

        # Check for fonts in visible text layers
        assert "ArialMT" in mapping

        # Check mapping structure
        for postscript_name, font_data in mapping.items():
            assert "family" in font_data
            assert "style" in font_data
            assert "weight" in font_data
            assert "_comment" in font_data

    def test_generate_only_missing(self) -> None:
        """Test generating mapping with only_missing=True."""
        psd_files = [Path("tests/fixtures/layer-types/type-layer.psd")]
        mapping = gfm.generate_mapping(psd_files, only_missing=True, verbose=False)

        # Should only include fonts NOT in default mapping
        # ArialMT is in default mapping, so should NOT be included
        assert "ArialMT" not in mapping

        # type-layer.psd only has ArialMT in visible layers, which is in default mapping
        # So the result should be empty when only_missing=True
        assert len(mapping) == 0

    def test_generate_empty_result(self, tmp_path: Path) -> None:
        """Test generating mapping when no fonts found."""
        # Create a PSD with no text layers (use a simple fixture)
        psd_files = [Path("tests/fixtures/basic.psd")]
        mapping = gfm.generate_mapping(psd_files, verbose=False)

        # Should return empty dict if no text layers
        assert isinstance(mapping, dict)

    def test_generate_validates_fonts_in_default(self) -> None:
        """Test that fonts in default mapping have correct structure."""
        psd_files = [Path("tests/fixtures/layer-types/type-layer.psd")]
        mapping = gfm.generate_mapping(psd_files, verbose=False)

        # Fonts in default mapping should have non-empty values
        if "ArialMT" in mapping:
            assert mapping["ArialMT"]["family"] == "Arial"
            assert mapping["ArialMT"]["style"] == "Regular"
            assert mapping["ArialMT"]["weight"] == 80.0
            assert "Found in default mapping" in mapping["ArialMT"]["_comment"]

    def test_generate_validates_fonts_not_in_default(self) -> None:
        """Test that fonts NOT in default mapping have empty template."""
        psd_files = [Path("tests/fixtures/layer-types/type-layer.psd")]
        mapping = gfm.generate_mapping(psd_files, verbose=False)

        # AdobeInvisFont is not in default mapping
        if "AdobeInvisFont" in mapping:
            assert mapping["AdobeInvisFont"]["family"] == ""
            assert mapping["AdobeInvisFont"]["style"] == ""
            assert mapping["AdobeInvisFont"]["weight"] == 0.0
            assert "Not in default mapping" in mapping["AdobeInvisFont"]["_comment"]


class TestMainCLI:
    """Tests for main CLI function."""

    def test_main_with_output_file(self, tmp_path: Path) -> None:
        """Test CLI with output file."""
        output_file = tmp_path / "fonts.json"
        psd_file = "tests/fixtures/layer-types/type-layer.psd"

        # Mock sys.argv
        original_argv = sys.argv
        try:
            sys.argv = ["generate_font_mapping", psd_file, "-o", str(output_file)]
            exit_code = gfm.main()

            assert exit_code == 0
            assert output_file.exists()

            # Verify JSON structure
            with open(output_file) as f:
                data = json.load(f)

            assert isinstance(data, dict)
            assert len(data) > 0

            # Check for known fonts
            assert "ArialMT" in data
        finally:
            sys.argv = original_argv

    def test_main_with_nonexistent_file(self) -> None:
        """Test CLI with nonexistent PSD file."""
        original_argv = sys.argv
        try:
            sys.argv = ["generate_font_mapping", "nonexistent.psd"]
            exit_code = gfm.main()

            # Should return error code
            assert exit_code == 1
        finally:
            sys.argv = original_argv

    def test_main_with_python_format(self, tmp_path: Path) -> None:
        """Test CLI with Python format output."""
        output_file = tmp_path / "fonts.py"
        psd_file = "tests/fixtures/layer-types/type-layer.psd"

        original_argv = sys.argv
        try:
            sys.argv = [
                "generate_font_mapping",
                psd_file,
                "-o",
                str(output_file),
                "--format",
                "python",
            ]
            exit_code = gfm.main()

            assert exit_code == 0
            assert output_file.exists()

            # Verify Python format
            content = output_file.read_text()
            assert "FONT_MAPPING = {" in content
            assert '"ArialMT"' in content
        finally:
            sys.argv = original_argv

    def test_main_with_only_missing_flag(self, tmp_path: Path) -> None:
        """Test CLI with --only-missing flag."""
        output_file = tmp_path / "fonts.json"
        psd_file = "tests/fixtures/layer-types/type-layer.psd"

        original_argv = sys.argv
        try:
            sys.argv = [
                "generate_font_mapping",
                psd_file,
                "-o",
                str(output_file),
                "--only-missing",
            ]
            exit_code = gfm.main()

            assert exit_code == 0

            # type-layer.psd only has ArialMT (which is in default mapping)
            # So with --only-missing, the result is empty and no file is written
            assert not output_file.exists()
        finally:
            sys.argv = original_argv
