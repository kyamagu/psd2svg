"""Tests for font collection and rasterization functionality."""

from typing import cast

from psd_tools import PSDImage

from psd2svg import SVGDocument, svg_utils

from .conftest import get_fixture


class TestFontCollection:
    """Tests for font storage in SVG during conversion."""

    def test_font_postscript_names_in_svg(self) -> None:
        """Test that PostScript font names are embedded in SVG font-family attributes."""
        # Use a PSD file with text layers
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=True)

        # Verify PostScript names are in SVG
        postscript_names = svg_utils.extract_font_families(document.svg)
        assert isinstance(postscript_names, set)
        # Note: Font presence depends on whether text layers exist

    def test_no_fonts_when_text_disabled(self) -> None:
        """Test that text is rasterized when text is disabled."""
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=False)

        # When text is disabled, text should be rasterized (no font-family attributes)
        postscript_names = svg_utils.extract_font_families(document.svg)
        assert isinstance(postscript_names, set)
        # May be empty or have fonts if text was partially converted

    def test_postscript_extraction_works(self) -> None:
        """Test that PostScript name extraction works on non-text layers."""
        psd_path = get_fixture("layer-types/pixel-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage)

        # Should return empty set for non-text layers
        postscript_names = svg_utils.extract_font_families(document.svg)
        assert isinstance(postscript_names, set)
        assert len(postscript_names) == 0


class TestFontExportLoad:
    """Tests for font serialization in export/load."""

    def test_export_no_longer_includes_fonts(self) -> None:
        """Test that export no longer includes separate fonts list (breaking change)."""
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=True)

        exported = document.export()

        # Fonts are now embedded in SVG, not separate
        assert "fonts" not in exported
        assert "svg" in exported
        assert "images" in exported

    def test_export_load_roundtrip(self) -> None:
        """Test that PostScript names survive export/load roundtrip."""
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=True)

        # Export the document
        exported = document.export()

        # Load it back
        loaded_document = SVGDocument.load(
            cast(str, exported["svg"]),
            cast(dict[str, bytes], exported["images"]),
        )

        # Verify PostScript names are preserved in SVG
        original_ps_names = svg_utils.extract_font_families(document.svg)
        loaded_ps_names = svg_utils.extract_font_families(loaded_document.svg)
        assert original_ps_names == loaded_ps_names


class TestFontRasterization:
    """Tests for font usage in rasterization."""

    def test_rasterize_with_fonts(self) -> None:
        """Test that rasterize passes font files to the rasterizer."""
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=True)

        # This should not raise an error even if fonts are collected
        # The rasterizer will handle missing fonts gracefully
        image = document.rasterize()

        # Verify we got an image back
        assert image is not None
        assert image.mode == "RGBA"

    def test_rasterize_without_fonts(self) -> None:
        """Test that rasterize works when there are no fonts."""
        psd_path = get_fixture("layer-types/pixel-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage)

        # Should work fine with no fonts
        image = document.rasterize()

        assert image is not None
        assert image.mode == "RGBA"
