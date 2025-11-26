"""Tests for font collection and rasterization functionality."""

from psd_tools import PSDImage

from psd2svg import SVGDocument
from psd2svg.core.font_utils import FontInfo

from .conftest import get_fixture


class TestFontCollection:
    """Tests for font collection during conversion."""

    def test_font_collection_from_text_layer(self) -> None:
        """Test that fonts are collected from text layers."""
        # Use a PSD file with text layers
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=True)

        # Verify fonts were collected
        assert isinstance(document.fonts, dict)
        # Note: Font collection depends on whether fonts are available on the system

    def test_no_fonts_when_text_disabled(self) -> None:
        """Test that fonts are not collected when text is disabled."""
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=False)

        # Fonts should be empty when text is disabled
        assert isinstance(document.fonts, dict)
        assert len(document.fonts) == 0

    def test_fonts_attribute_exists(self) -> None:
        """Test that SVGDocument has fonts attribute."""
        psd_path = get_fixture("layer-types/pixel-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage)

        # Fonts should be an empty dict for non-text layers
        assert hasattr(document, "fonts")
        assert isinstance(document.fonts, dict)
        assert len(document.fonts) == 0


class TestFontExportLoad:
    """Tests for font serialization in export/load."""

    def test_export_includes_fonts(self) -> None:
        """Test that export includes fonts in the result."""
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=True)

        exported = document.export()

        # Verify fonts are in the export
        assert "fonts" in exported
        assert isinstance(exported["fonts"], dict)

    def test_export_load_roundtrip(self) -> None:
        """Test that fonts survive export/load roundtrip."""
        psd_path = get_fixture("layer-types/type-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage, enable_text=True)

        # Export the document
        exported = document.export()

        # Load it back
        loaded_document = SVGDocument.load(
            exported["svg"], exported["images"], exported["fonts"]
        )

        # Verify fonts are preserved
        assert isinstance(loaded_document.fonts, dict)
        assert len(loaded_document.fonts) == len(document.fonts)

        # Verify font info objects are correctly reconstructed
        for postscript_name, font_info in loaded_document.fonts.items():
            assert isinstance(font_info, FontInfo)
            assert font_info.postscript_name == postscript_name

    def test_load_without_fonts_param(self) -> None:
        """Test that load works without fonts parameter (backward compatibility)."""
        psd_path = get_fixture("layer-types/pixel-layer.psd")
        psdimage = PSDImage.open(psd_path)
        document = SVGDocument.from_psd(psdimage)

        exported = document.export()

        # Load without fonts parameter
        loaded_document = SVGDocument.load(exported["svg"], exported["images"])

        # Should have empty fonts dict
        assert isinstance(loaded_document.fonts, dict)
        assert len(loaded_document.fonts) == 0


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
