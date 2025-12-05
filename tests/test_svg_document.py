"""Tests for SVGDocument class functionality.

This module tests various SVGDocument methods including:
- Font encoding and embedding (@font-face CSS generation)
- Image handling (embedding vs file saving)
- String and file serialization (tostring, save)
- Rasterization with different backends
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from psd2svg import SVGDocument
from psd2svg.core.font_utils import FontInfo, encode_font_data_uri


class TestEncodeFontDataUri:
    """Tests for encode_font_data_uri function."""

    def test_encode_ttf_font(self, tmp_path: Path) -> None:
        """Test encoding TTF font file to data URI."""
        # Create a minimal fake TTF file
        font_file = tmp_path / "test.ttf"
        font_file.write_bytes(b"FAKE_TTF_DATA")

        data_uri = encode_font_data_uri(str(font_file))

        assert data_uri.startswith("data:font/ttf;base64,")
        assert "RkFLRV9UVEZfREFUQQ==" in data_uri  # base64 of "FAKE_TTF_DATA"

    def test_encode_otf_font(self, tmp_path: Path) -> None:
        """Test encoding OTF font file uses correct MIME type."""
        font_file = tmp_path / "test.otf"
        font_file.write_bytes(b"FAKE_OTF_DATA")

        data_uri = encode_font_data_uri(str(font_file))

        assert data_uri.startswith("data:font/otf;base64,")

    def test_encode_woff_font(self, tmp_path: Path) -> None:
        """Test encoding WOFF font file uses correct MIME type."""
        font_file = tmp_path / "test.woff"
        font_file.write_bytes(b"FAKE_WOFF_DATA")

        data_uri = encode_font_data_uri(str(font_file))

        assert data_uri.startswith("data:font/woff;base64,")

    def test_encode_woff2_font(self, tmp_path: Path) -> None:
        """Test encoding WOFF2 font file uses correct MIME type."""
        font_file = tmp_path / "test.woff2"
        font_file.write_bytes(b"FAKE_WOFF2_DATA")

        data_uri = encode_font_data_uri(str(font_file))

        assert data_uri.startswith("data:font/woff2;base64,")

    def test_encode_unknown_extension_defaults_to_ttf(self, tmp_path: Path) -> None:
        """Test unknown font extension defaults to font/ttf MIME type."""
        font_file = tmp_path / "test.xyz"
        font_file.write_bytes(b"UNKNOWN_FONT_DATA")

        data_uri = encode_font_data_uri(str(font_file))

        assert data_uri.startswith("data:font/ttf;base64,")

    def test_encode_nonexistent_font_raises_error(self) -> None:
        """Test encoding non-existent font file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Font file not found"):
            encode_font_data_uri("/nonexistent/path/to/font.ttf")

    def test_encode_unreadable_font_raises_error(self, tmp_path: Path) -> None:
        """Test encoding unreadable font file raises IOError."""
        font_file = tmp_path / "test.ttf"
        font_file.write_bytes(b"FAKE_TTF_DATA")

        # Make file unreadable (only works on Unix-like systems)
        import os
        import sys

        if sys.platform != "win32":
            os.chmod(font_file, 0o000)
            try:
                with pytest.raises(IOError, match="Failed to read font file"):
                    encode_font_data_uri(str(font_file))
            finally:
                # Restore permissions for cleanup
                os.chmod(font_file, 0o644)


class TestFontInfoToFontFaceCss:
    """Tests for FontInfo.to_font_face_css method."""

    def test_to_font_face_css_regular(self) -> None:
        """Test CSS generation for regular font."""
        font = FontInfo(
            postscript_name="ArialMT",
            file="/path/to/arial.ttf",
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        css = font.to_font_face_css("data:font/ttf;base64,ABC123")

        assert "@font-face {" in css
        assert "font-family: 'Arial';" in css
        assert "src: url(data:font/ttf;base64,ABC123);" in css
        assert "font-weight: 400;" in css
        assert "font-style: normal;" in css
        assert "}" in css

    def test_to_font_face_css_bold(self) -> None:
        """Test CSS generation for bold font."""
        font = FontInfo(
            postscript_name="Arial-BoldMT",
            file="/path/to/arial-bold.ttf",
            family="Arial",
            style="Bold",
            weight=200.0,
        )

        css = font.to_font_face_css("data:font/ttf;base64,XYZ789")

        assert "font-weight: 700;" in css
        assert "font-style: normal;" in css

    def test_to_font_face_css_italic(self) -> None:
        """Test CSS generation for italic font."""
        font = FontInfo(
            postscript_name="Arial-ItalicMT",
            file="/path/to/arial-italic.ttf",
            family="Arial",
            style="Italic",
            weight=80.0,
        )

        css = font.to_font_face_css("data:font/ttf;base64,DEF456")

        assert "font-weight: 400;" in css
        assert "font-style: italic;" in css

    def test_to_font_face_css_bold_italic(self) -> None:
        """Test CSS generation for bold italic font."""
        font = FontInfo(
            postscript_name="Arial-BoldItalicMT",
            file="/path/to/arial-bolditalic.ttf",
            family="Arial",
            style="Bold Italic",
            weight=200.0,
        )

        css = font.to_font_face_css("data:font/ttf;base64,GHI012")

        assert "font-weight: 700;" in css
        assert "font-style: italic;" in css


class TestSVGDocumentImageHandling:
    """Tests for SVGDocument image handling behavior."""

    def test_tostring_default_no_images(self) -> None:
        """Test tostring() with default parameters works when no images present."""
        svg_elem = ET.Element("svg")
        ET.SubElement(svg_elem, "rect", x="10", y="10", width="80", height="80")

        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        # Should work with no parameters (embed_images=True by default)
        result = document.tostring()

        assert "<svg>" in result
        assert "<rect" in result
        assert 'x="10"' in result

    def test_tostring_default_with_images(self) -> None:
        """Test tostring() with default parameters embeds images."""
        svg_elem = ET.Element("svg")
        ET.SubElement(svg_elem, "image", id="image")

        document = SVGDocument(
            svg=svg_elem,
            images={"image": Image.new("RGB", (10, 10), color="red")},
            fonts=[],
        )

        # Should embed images by default
        result = document.tostring()

        assert "data:image/webp;base64," in result
        assert "href=" in result

    def test_tostring_embed_images_false_no_prefix_raises_error(self) -> None:
        """Test tostring() with embed_images=False and no prefix raises error."""
        svg_elem = ET.Element("svg")
        ET.SubElement(svg_elem, "image", id="image")

        document = SVGDocument(
            svg=svg_elem,
            images={"image": Image.new("RGB", (10, 10), color="red")},
            fonts=[],
        )

        # Should raise ValueError when images exist but no output method specified
        with pytest.raises(
            ValueError,
            match="Either embed_images must be True or image_prefix must be provided",
        ):
            document.tostring(embed_images=False)

    def test_tostring_with_image_prefix_saves_files(self, tmp_path: Path) -> None:
        """Test tostring() with image_prefix saves images to files."""
        svg_elem = ET.Element("svg")
        ET.SubElement(svg_elem, "image", id="image")

        document = SVGDocument(
            svg=svg_elem,
            images={"image": Image.new("RGB", (10, 10), color="blue")},
            fonts=[],
        )

        # Use image_prefix to save files
        prefix = str(tmp_path / "img")
        result = document.tostring(image_prefix=prefix)

        # Should contain filename reference, not data URI
        assert "data:image/" not in result
        assert "img01.webp" in result

        # File should be created
        assert (tmp_path / "img01.webp").exists()

    def test_handle_images_empty_document(self) -> None:
        """Test _handle_images() returns early when no images present."""
        svg_elem = ET.Element("svg")
        ET.SubElement(svg_elem, "rect")

        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        # Should work with any combination when no images
        result1 = document.tostring(embed_images=True)
        result2 = document.tostring(embed_images=False)

        assert "<rect" in result1
        assert "<rect" in result2
        # Both should produce same output since no images to handle
        assert result1 == result2


class TestSVGDocumentEmbedFonts:
    """Tests for SVGDocument font embedding functionality."""

    def test_tostring_with_embed_fonts_false(self) -> None:
        """Test tostring with embed_fonts=False doesn't add style element."""
        svg_elem = ET.Element("svg")
        ET.SubElement(svg_elem, "rect")

        document = SVGDocument(svg=svg_elem, images={}, fonts=[])
        result = document.tostring(embed_images=True, embed_fonts=False)

        assert "<style>" not in result
        assert "@font-face" not in result

    def test_tostring_with_embed_fonts_true_no_fonts(self) -> None:
        """Test tostring with embed_fonts=True but no fonts doesn't add style element."""
        svg_elem = ET.Element("svg")
        ET.SubElement(svg_elem, "rect")

        document = SVGDocument(svg=svg_elem, images={}, fonts=[])
        result = document.tostring(embed_images=True, embed_fonts=True)

        assert "<style>" not in result

    @patch("psd2svg.core.font_utils.encode_font_data_uri")
    def test_tostring_with_embed_fonts_true(
        self, mock_encode: MagicMock, tmp_path: Path
    ) -> None:
        """Test tostring with embed_fonts=True adds style element."""
        mock_encode.return_value = "data:font/ttf;base64,MOCKDATA"

        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"FAKE_FONT")

        svg_elem = ET.Element("svg")
        font = FontInfo(
            postscript_name="ArialMT",
            file=str(font_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        document = SVGDocument(svg=svg_elem, images={}, fonts=[font])
        result = document.tostring(
            embed_images=True, embed_fonts=True, subset_fonts=False
        )

        assert "<style>" in result
        assert "@font-face" in result
        assert "font-family: 'Arial'" in result
        assert "data:font/ttf;base64,MOCKDATA" in result
        mock_encode.assert_called_once_with(str(font_file))

    @patch("psd2svg.core.font_utils.encode_font_data_uri")
    def test_save_with_embed_fonts_true(
        self, mock_encode: MagicMock, tmp_path: Path
    ) -> None:
        """Test save with embed_fonts=True writes style element to file."""
        mock_encode.return_value = "data:font/ttf;base64,MOCKDATA"

        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"FAKE_FONT")
        output_file = tmp_path / "output.svg"

        svg_elem = ET.Element("svg")
        font = FontInfo(
            postscript_name="ArialMT",
            file=str(font_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        document = SVGDocument(svg=svg_elem, images={}, fonts=[font])
        document.save(
            str(output_file), embed_images=True, embed_fonts=True, subset_fonts=False
        )

        content = output_file.read_text()
        assert "<style>" in content
        assert "@font-face" in content
        assert "font-family: 'Arial'" in content

    @patch("psd2svg.core.font_utils.encode_font_data_uri")
    def test_embed_fonts_deduplicates_same_font(
        self, mock_encode: MagicMock, tmp_path: Path
    ) -> None:
        """Test that duplicate fonts are not embedded multiple times."""
        mock_encode.return_value = "data:font/ttf;base64,MOCKDATA"

        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"FAKE_FONT")

        svg_elem = ET.Element("svg")
        # Create two FontInfo objects pointing to the same file
        font1 = FontInfo(
            postscript_name="ArialMT",
            file=str(font_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        font2 = FontInfo(
            postscript_name="ArialMT",
            file=str(font_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        document = SVGDocument(svg=svg_elem, images={}, fonts=[font1, font2])
        result = document.tostring(
            embed_images=True, embed_fonts=True, subset_fonts=False
        )

        # Should only encode once
        mock_encode.assert_called_once()

        # Should only have one @font-face rule
        assert result.count("@font-face") == 1

    @patch("psd2svg.core.font_utils.encode_font_data_uri")
    def test_embed_fonts_caches_encoded_data(
        self, mock_encode: MagicMock, tmp_path: Path
    ) -> None:
        """Test that encoded font data is cached across multiple calls."""
        mock_encode.return_value = "data:font/ttf;base64,MOCKDATA"

        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"FAKE_FONT")

        svg_elem = ET.Element("svg")
        font = FontInfo(
            postscript_name="ArialMT",
            file=str(font_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        document = SVGDocument(svg=svg_elem, images={}, fonts=[font])

        # Call tostring twice
        document.tostring(embed_images=True, embed_fonts=True, subset_fonts=False)
        document.tostring(embed_images=True, embed_fonts=True, subset_fonts=False)

        # Should only encode once due to caching
        mock_encode.assert_called_once()

    @patch("psd2svg.core.font_utils.encode_font_data_uri")
    def test_embed_fonts_handles_missing_font_gracefully(
        self, mock_encode: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that missing fonts are skipped with a warning."""
        mock_encode.side_effect = FileNotFoundError("Font not found")

        svg_elem = ET.Element("svg")
        font = FontInfo(
            postscript_name="MissingFont",
            file="/nonexistent/font.ttf",
            family="Missing",
            style="Regular",
            weight=80.0,
        )

        document = SVGDocument(svg=svg_elem, images={}, fonts=[font])
        result = document.tostring(
            embed_images=True, embed_fonts=True, subset_fonts=False
        )

        # Should not raise exception
        assert "<style>" not in result

        # Should log warning about no fonts embedded (font is skipped early because file doesn't exist)
        assert "No fonts were successfully embedded" in caplog.text

    @patch("psd2svg.core.font_utils.encode_font_data_uri")
    def test_embed_fonts_with_multiple_fonts(
        self, mock_encode: MagicMock, tmp_path: Path
    ) -> None:
        """Test embedding multiple different fonts."""

        def mock_encode_func(path: str) -> str:
            return f"data:font/ttf;base64,MOCK_{Path(path).stem}"

        mock_encode.side_effect = mock_encode_func

        font1_file = tmp_path / "arial.ttf"
        font1_file.write_bytes(b"FAKE_FONT1")
        font2_file = tmp_path / "times.ttf"
        font2_file.write_bytes(b"FAKE_FONT2")

        svg_elem = ET.Element("svg")
        font1 = FontInfo(
            postscript_name="ArialMT",
            file=str(font1_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        font2 = FontInfo(
            postscript_name="TimesNewRomanMT",
            file=str(font2_file),
            family="Times New Roman",
            style="Regular",
            weight=80.0,
        )

        document = SVGDocument(svg=svg_elem, images={}, fonts=[font1, font2])
        result = document.tostring(
            embed_images=True, embed_fonts=True, subset_fonts=False
        )

        assert result.count("@font-face") == 2
        assert "font-family: 'Arial'" in result
        assert "font-family: 'Times New Roman'" in result
        assert "MOCK_arial" in result
        assert "MOCK_times" in result


class TestSVGDocumentRasterizeWithFonts:
    """Tests for font embedding in rasterize() method."""

    @patch("psd2svg.core.font_utils.encode_font_data_uri")
    def test_rasterize_with_resvg_uses_font_files(
        self, mock_encode: MagicMock, tmp_path: Path
    ) -> None:
        """Test that ResvgRasterizer receives font files directly."""
        from psd2svg.rasterizer import ResvgRasterizer

        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"FAKE_FONT")

        svg_elem = ET.Element("svg", width="100", height="100")
        font = FontInfo(
            postscript_name="ArialMT",
            file=str(font_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        document = SVGDocument(svg=svg_elem, images={}, fonts=[font])

        with patch.object(ResvgRasterizer, "from_string") as mock_from_string:
            mock_from_string.return_value = Image.new("RGBA", (100, 100))

            rasterizer = ResvgRasterizer()
            document.rasterize(rasterizer=rasterizer)

            # Should pass font_files to from_string
            assert mock_from_string.call_count == 1
            call_kwargs = mock_from_string.call_args[1]
            assert "font_files" in call_kwargs
            assert call_kwargs["font_files"] == [str(font_file)]

            # Should NOT embed fonts in SVG
            svg_arg = mock_from_string.call_args[0][0]
            assert "@font-face" not in svg_arg

    @patch("psd2svg.core.font_utils.encode_font_data_uri")
    def test_rasterize_with_playwright_embeds_fonts(
        self, mock_encode: MagicMock, tmp_path: Path
    ) -> None:
        """Test that PlaywrightRasterizer gets fonts embedded in SVG."""
        try:
            from psd2svg.rasterizer import PlaywrightRasterizer
        except ImportError:
            pytest.skip("PlaywrightRasterizer not available")

        mock_encode.return_value = "data:font/ttf;base64,MOCKDATA"

        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"FAKE_FONT")

        svg_elem = ET.Element("svg", width="100", height="100")
        font = FontInfo(
            postscript_name="ArialMT",
            file=str(font_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )

        document = SVGDocument(svg=svg_elem, images={}, fonts=[font])

        with patch.object(PlaywrightRasterizer, "from_string") as mock_from_string:
            mock_from_string.return_value = Image.new("RGBA", (100, 100))

            rasterizer = PlaywrightRasterizer()
            document.rasterize(rasterizer=rasterizer)

            # Should embed fonts in SVG
            assert mock_from_string.call_count == 1
            svg_arg = mock_from_string.call_args[0][0]
            assert "@font-face" in svg_arg
            assert "font-family: 'Arial'" in svg_arg
            assert "data:font/ttf;base64,MOCKDATA" in svg_arg


class TestAppendCss:
    """Tests for SVGDocument.append_css method."""

    def test_append_css_basic(self) -> None:
        """Test basic CSS injection into SVG."""
        svg_elem = ET.Element("svg", width="100", height="100")
        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        css = "text { font-variant-east-asian: proportional-width; }"
        document.append_css(css)

        svg_string = document.tostring()
        assert "<style>" in svg_string
        assert "font-variant-east-asian: proportional-width" in svg_string

    def test_append_css_creates_style_element(self) -> None:
        """Test that append_css creates <style> element if not present."""
        svg_elem = ET.Element("svg", width="100", height="100")
        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        # Initially no style element
        style_elem = svg_elem.find("style")
        assert style_elem is None

        document.append_css("text { color: red; }")

        # Now style element should exist
        style_elem = svg_elem.find("style")
        assert style_elem is not None
        assert style_elem.text is not None
        assert "text { color: red; }" in style_elem.text

    def test_append_css_multiple_calls(self) -> None:
        """Test that multiple append_css calls accumulate CSS."""
        svg_elem = ET.Element("svg", width="100", height="100")
        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        document.append_css("text { color: red; }")
        document.append_css("rect { fill: blue; }")

        svg_string = document.tostring()
        assert "text { color: red; }" in svg_string
        assert "rect { fill: blue; }" in svg_string

    def test_append_css_idempotent(self) -> None:
        """Test that appending the same CSS multiple times is idempotent."""
        svg_elem = ET.Element("svg", width="100", height="100")
        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        css = "text { font-variant-east-asian: proportional-width; }"
        document.append_css(css)
        document.append_css(css)
        document.append_css(css)

        svg_string = document.tostring()
        # Should only appear once (duplicate detection)
        count = svg_string.count("font-variant-east-asian: proportional-width")
        assert count == 1

    def test_append_css_with_media_query(self) -> None:
        """Test appending CSS with media query."""
        svg_elem = ET.Element("svg", width="100", height="100")
        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        css = "@media print { .no-print { display: none; } }"
        document.append_css(css)

        svg_string = document.tostring()
        assert "@media print" in svg_string
        assert "no-print" in svg_string

    def test_append_css_with_font_embedding(self, tmp_path: Path) -> None:
        """Test that append_css works alongside font embedding."""
        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"FAKE_FONT")

        svg_elem = ET.Element("svg", width="100", height="100")
        font = FontInfo(
            postscript_name="ArialMT",
            file=str(font_file),
            family="Arial",
            style="Regular",
            weight=80.0,
        )
        document = SVGDocument(svg=svg_elem, images={}, fonts=[font])

        # Add custom CSS
        document.append_css("text { font-variant-east-asian: proportional-width; }")

        # Get string with font embedding
        with patch("psd2svg.core.font_utils.encode_font_data_uri") as mock_encode:
            mock_encode.return_value = "data:font/ttf;base64,MOCKDATA"
            svg_string = document.tostring(embed_fonts=True)

        # Should contain both custom CSS and font-face
        assert "font-variant-east-asian: proportional-width" in svg_string
        assert "@font-face" in svg_string
        assert "font-family: 'Arial'" in svg_string

    def test_append_css_empty_string(self) -> None:
        """Test that appending empty CSS string doesn't cause issues."""
        svg_elem = ET.Element("svg", width="100", height="100")
        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        document.append_css("")

        svg_string = document.tostring()
        # Should work without errors (may or may not create style element)
        assert "<svg" in svg_string

    def test_append_css_with_save(self, tmp_path: Path) -> None:
        """Test that append_css works with save method."""
        svg_elem = ET.Element("svg", width="100", height="100")
        document = SVGDocument(svg=svg_elem, images={}, fonts=[])

        document.append_css("text { color: green; }")

        output_file = tmp_path / "output.svg"
        document.save(str(output_file))

        # Read file and verify CSS is present
        svg_content = output_file.read_text()
        assert "text { color: green; }" in svg_content
