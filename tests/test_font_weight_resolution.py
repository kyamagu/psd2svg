"""Tests for font-weight and font-style resolution after PostScript name resolution."""

import xml.etree.ElementTree as ET

from psd2svg import SVGDocument


class TestFontWeightResolution:
    """Tests for font-weight and font-style attributes after PostScript resolution."""

    def test_bold_font_weight_set_after_resolution(self) -> None:
        """Test that font-weight is set when resolving bold PostScript names."""
        # Create SVG with bold PostScript name
        svg_str = '<svg xmlns="http://www.w3.org/2000/svg"><text font-family="Arial-BoldMT">Bold Text</text></svg>'
        svg = ET.fromstring(svg_str)
        doc = SVGDocument(svg=svg, images={})

        # Resolve PostScript names
        doc._resolve_postscript_names(svg)

        # Find text element (need namespace-aware search)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        text = svg.find(".//svg:text", ns)
        assert text is not None

        # Check that font-family was resolved and font-weight was set
        assert text.get("font-family") == "'Arial'"
        assert text.get("font-weight") == "700"  # Bold

    def test_italic_font_style_set_after_resolution(self) -> None:
        """Test that font-style is set when resolving italic PostScript names."""
        svg_str = '<svg xmlns="http://www.w3.org/2000/svg"><text font-family="Arial-ItalicMT">Italic Text</text></svg>'
        svg = ET.fromstring(svg_str)
        doc = SVGDocument(svg=svg, images={})

        doc._resolve_postscript_names(svg)

        ns = {"svg": "http://www.w3.org/2000/svg"}
        text = svg.find(".//svg:text", ns)
        assert text is not None
        assert text.get("font-family") == "'Arial'"
        assert text.get("font-style") == "italic"

    def test_bold_italic_both_set_after_resolution(self) -> None:
        """Test that both font-weight and font-style are set."""
        svg_str = '<svg xmlns="http://www.w3.org/2000/svg"><text font-family="Arial-BoldItalicMT">Bold Italic</text></svg>'
        svg = ET.fromstring(svg_str)
        doc = SVGDocument(svg=svg, images={})

        doc._resolve_postscript_names(svg)

        ns = {"svg": "http://www.w3.org/2000/svg"}
        text = svg.find(".//svg:text", ns)
        assert text is not None
        assert text.get("font-family") == "'Arial'"
        assert text.get("font-weight") == "700"
        assert text.get("font-style") == "italic"

    def test_regular_font_no_weight_style(self) -> None:
        """Test that regular fonts don't get unnecessary attributes."""
        svg_str = '<svg xmlns="http://www.w3.org/2000/svg"><text font-family="ArialMT">Regular Text</text></svg>'
        svg = ET.fromstring(svg_str)
        doc = SVGDocument(svg=svg, images={})

        doc._resolve_postscript_names(svg)

        ns = {"svg": "http://www.w3.org/2000/svg"}
        text = svg.find(".//svg:text", ns)
        assert text is not None
        assert text.get("font-family") == "'Arial'"
        assert text.get("font-weight") is None  # No attribute for 400 (Regular)
        assert text.get("font-style") is None

    def test_preserve_existing_faux_bold(self) -> None:
        """Test that existing font-weight (faux bold) is preserved."""
        svg_str = '<svg xmlns="http://www.w3.org/2000/svg"><text font-family="ArialMT" font-weight="bold">Text</text></svg>'
        svg = ET.fromstring(svg_str)
        doc = SVGDocument(svg=svg, images={})

        doc._resolve_postscript_names(svg)

        ns = {"svg": "http://www.w3.org/2000/svg"}
        text = svg.find(".//svg:text", ns)
        assert text is not None
        assert text.get("font-family") == "'Arial'"
        assert text.get("font-weight") == "bold"  # Preserved from original (faux bold)

    def test_preserve_existing_faux_italic(self) -> None:
        """Test that existing font-style (faux italic) is preserved."""
        svg_str = '<svg xmlns="http://www.w3.org/2000/svg"><text font-family="ArialMT" font-style="italic">Text</text></svg>'
        svg = ET.fromstring(svg_str)
        doc = SVGDocument(svg=svg, images={})

        doc._resolve_postscript_names(svg)

        ns = {"svg": "http://www.w3.org/2000/svg"}
        text = svg.find(".//svg:text", ns)
        assert text is not None
        assert text.get("font-family") == "'Arial'"
        assert (
            text.get("font-style") == "italic"
        )  # Preserved from original (faux italic)

    def test_various_font_weights(self) -> None:
        """Test that various font weights are correctly set."""
        test_cases = [
            # (PostScript name, expected family, expected weight)
            ("ArialMT", "'Arial'", None),  # 400 = Regular, no attribute
            ("Arial-BoldMT", "'Arial'", "700"),  # Bold
            ("TimesNewRomanPSMT", "'Times New Roman'", None),  # Regular
            ("TimesNewRomanPS-BoldMT", "'Times New Roman'", "700"),  # Bold
        ]

        for ps_name, expected_family, expected_weight in test_cases:
            svg_str = f'<svg xmlns="http://www.w3.org/2000/svg"><text font-family="{ps_name}">Text</text></svg>'
            svg = ET.fromstring(svg_str)
            doc = SVGDocument(svg=svg, images={})

            doc._resolve_postscript_names(svg)

            ns = {"svg": "http://www.w3.org/2000/svg"}
            text = svg.find(".//svg:text", ns)
            assert text is not None
            assert text.get("font-family") == expected_family, f"Failed for {ps_name}"
            assert text.get("font-weight") == expected_weight, (
                f"Failed weight for {ps_name}"
            )

    def test_multiple_elements_same_font(self) -> None:
        """Test that all elements with same PostScript name get weight/style."""
        svg_str = """<svg xmlns="http://www.w3.org/2000/svg">
            <text font-family="Arial-BoldMT">Text 1</text>
            <text font-family="Arial-BoldMT">Text 2</text>
            <text font-family="Arial-BoldMT">Text 3</text>
        </svg>"""
        svg = ET.fromstring(svg_str)
        doc = SVGDocument(svg=svg, images={})

        doc._resolve_postscript_names(svg)

        ns = {"svg": "http://www.w3.org/2000/svg"}
        texts = svg.findall(".//svg:text", ns)
        assert len(texts) == 3

        for text in texts:
            assert text.get("font-family") == "'Arial'"
            assert text.get("font-weight") == "700"
