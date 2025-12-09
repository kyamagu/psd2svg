import dataclasses
import logging
import os
import xml.etree.ElementTree as ET
from copy import deepcopy

from PIL import Image
from psd_tools import PSDImage

from psd2svg import image_utils, svg_utils
from psd2svg.core import font_utils
from psd2svg.core.converter import Converter
from psd2svg.core.font_utils import FontInfo
from psd2svg.rasterizer import BaseRasterizer, ResvgRasterizer

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_FORMAT = "webp"


@dataclasses.dataclass
class SVGDocument:
    """SVG document and resources.

    Example usage::

        from psd_tools import PSDImage
        from psd2svg import SVGDocument

        # Create from PSDImage.
        psdimage = PSDImage.open("input.psd")
        document = SVGDocument.from_psd(psdimage)

        # Save to file or get as string.
        document.save("output.svg")  # Images embedded by default
        svg_string = document.tostring()

        # Rasterize to PIL Image.
        rasterized = document.rasterize()

        # Export and load back.
        exported = document.export()
        document = SVGDocument.load(exported["svg"], exported["images"])
    """

    svg: ET.Element
    images: dict[str, Image.Image] = dataclasses.field(default_factory=dict)
    # Note: fonts property removed - PostScript names stored directly in SVG font-family attributes
    _font_data_cache: dict[str, str] = dataclasses.field(
        default_factory=dict, init=False, repr=False
    )

    @staticmethod
    def from_psd(
        psdimage: PSDImage,
        enable_live_shapes: bool = True,
        enable_text: bool = True,
        enable_title: bool = False,
        enable_class: bool = False,
        text_letter_spacing_offset: float = 0.0,
        text_wrapping_mode: int = 0,
        font_mapping: dict[str, dict[str, float | str]] | None = None,
        enable_fontconfig: bool = True,
    ) -> "SVGDocument":
        """Create a new SVGDocument from a PSDImage.

        Args:
            psdimage: PSDImage object to convert.
            enable_live_shapes: Enable live shape conversion when possible.
                Disabling live shapes results in <path> elements instead of
                shape primitives like <rect> or <circle>. This may be more
                accurate, but less editable.
            enable_text: Enable text layer conversion. If False, text layers
                are rasterized as images.
            enable_title: Enable insertion of <title> elements with layer names.
                When False (default), title elements are omitted to reduce file size.
                Set to True to include <title> elements containing the Photoshop layer
                name for accessibility and debugging.
            enable_class: Enable insertion of class attributes on SVG elements for
                debugging purposes. When False (default), elements will not have class
                attributes, producing cleaner SVG output. Set to True to add class
                attributes for layer types, effects, and semantic roles (e.g.,
                "shape-layer", "drop-shadow-effect", "fill") for debugging or styling.
            text_letter_spacing_offset: Global offset (in pixels) to add to all
                letter-spacing values. This can be used to compensate for differences
                between Photoshop's text rendering and SVG's text rendering. Typical
                values range from -0.02 to 0.02. Default is 0.0 (no offset).
            text_wrapping_mode: Text wrapping mode for bounding box text. Use 0 for no
                wrapping (default, native SVG <text>), or 1 for <foreignObject> with
                XHTML wrapping. Import TextWrappingMode from psd2svg.core.text for
                enum values. Only affects bounding box text (ShapeType=1); point text
                always uses native SVG <text> elements.
            font_mapping: Optional custom font mapping dictionary for resolving PostScript
                font names to font families without fontconfig. Useful on Windows or when
                fonts are not installed. Format:
                {"PostScriptName": {"family": str, "style": str, "weight": float}}.
                Example: {"ArialMT": {"family": "Arial", "style": "Regular", "weight": 80.0}}.
                When not provided, uses built-in mapping for common fonts.
            enable_fontconfig: If True (default), fall back to fontconfig for fonts not in
                static mapping. If False, only use static/custom mapping. Setting to False
                can prevent unexpected font substitutions when fontconfig is available.
        Returns:
            SVGDocument object containing the converted SVG and images.
        """
        # Build SVG tree with original font names
        converter = Converter(
            psdimage,
            enable_live_shapes=enable_live_shapes,
            enable_text=enable_text,
            enable_title=enable_title,
            enable_class=enable_class,
            text_letter_spacing_offset=text_letter_spacing_offset,
            text_wrapping_mode=text_wrapping_mode,
            font_mapping=font_mapping,
            enable_fontconfig=enable_fontconfig,
        )
        converter.build()

        document = SVGDocument(
            svg=converter.svg,
            images=converter.images,
        )

        return document

    def append_css(self, css: str) -> None:
        """Append custom CSS rules to the SVG <style> element.

        This method allows you to inject custom CSS rules into the SVG document.
        The CSS is appended to an existing <style> element if present, or a new
        <style> element is created as the first child of the root SVG element.

        Args:
            css: CSS rules to append. Can be any valid CSS including selectors,
                media queries, keyframes, etc.

        Example:
            >>> from psd_tools import PSDImage
            >>> from psd2svg import SVGDocument
            >>>
            >>> psdimage = PSDImage.open("input.psd")
            >>> svg_doc = SVGDocument.from_psd(psdimage)
            >>>
            >>> # Add custom CSS for Japanese text
            >>> svg_doc.append_css("text { font-variant-east-asian: proportional-width; }")
            >>>
            >>> # Add more custom CSS
            >>> svg_doc.append_css("@media print { .no-print { display: none; } }")
            >>>
            >>> svg_doc.save("output.svg")

        Note:
            This method is idempotent - if the same CSS is appended multiple times,
            it will only appear once in the output (duplicate detection).
        """
        svg_utils.insert_or_update_style_element(self.svg, css)

    def tostring(
        self,
        embed_images: bool = True,
        embed_fonts: bool = False,
        subset_fonts: bool = True,
        font_format: str = "woff2",
        image_prefix: str | None = None,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
        optimize: bool = True,
    ) -> str:
        """Convert SVG document to string.

        Args:
            embed_images: If True, embed images as base64 data URIs. Default is True
                since string output has no file system context for external images.
            embed_fonts: If True, embed fonts as @font-face rules in <style> element.
                WARNING: Font embedding may be subject to licensing restrictions.
                Ensure you have appropriate rights before distributing SVG files
                with embedded fonts.
            subset_fonts: If True, subset fonts to only include glyphs used in the SVG.
                Requires embed_fonts=True. Requires fonttools package (install with:
                uv sync --group fonts). This significantly reduces file size (typically
                90%+ reduction). Default is True.
            font_format: Font format for embedding: "woff2" (default), "woff", "ttf", or "otf".
                WOFF2 provides best compression and is recommended for web use.
            image_prefix: If provided, save images to files with this prefix.
                When specified, embed_images is ignored.
            image_format: Image format to use when embedding or saving images.
            indent: Indentation string for pretty-printing the SVG.
            optimize: If True, apply SVG optimizations (consolidate defs, etc.).
                Default is True.
        """
        # Create a copy to avoid modifying the original SVG
        svg = deepcopy(self.svg)

        svg = self._handle_images(
            svg, embed_images, image_prefix, image_format, svg_filepath=None
        )

        # Always resolve PostScript names to CSS font families
        self._resolve_postscript_names(svg)

        if embed_fonts:
            self._insert_css_fontface(
                svg,
                subset_fonts=subset_fonts,
                font_format=font_format,
                use_data_uri=True,
            )

        if optimize:
            svg_utils.consolidate_defs(svg)

        return svg_utils.tostring(svg, indent=indent)

    def save(
        self,
        filepath: str,
        embed_images: bool = True,
        embed_fonts: bool = False,
        subset_fonts: bool = True,
        font_format: str = "woff2",
        image_prefix: str | None = None,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
        optimize: bool = True,
    ) -> None:
        """Save the SVG to a file.

        Args:
            filepath: Path to the output SVG file.
            embed_images: If True, embed images as base64 data URIs. Default is True.
                Set to False and provide image_prefix to save images as external files.
            embed_fonts: If True, embed fonts as @font-face rules in <style> element.
                WARNING: Font embedding may be subject to licensing restrictions.
                Ensure you have appropriate rights before distributing SVG files
                with embedded fonts.
            subset_fonts: If True, subset fonts to only include glyphs used in the SVG.
                Requires embed_fonts=True. Requires fonttools package (install with:
                uv sync --group fonts). This significantly reduces file size (typically
                90%+ reduction). Default is True.
            font_format: Font format for embedding: "woff2" (default), "woff", "ttf", or "otf".
                WOFF2 provides best compression and is recommended for web use.
            image_prefix: If provided, save images to files with this prefix
                relative to the output SVG file's directory.
            image_format: Image format to use when embedding or saving images.
            indent: Indentation string for pretty-printing the SVG.
            optimize: If True, apply SVG optimizations (consolidate defs, etc.).
                Default is True.
        """
        # Create a copy to avoid modifying the original SVG
        svg = deepcopy(self.svg)

        svg = self._handle_images(
            svg, embed_images, image_prefix, image_format, svg_filepath=filepath
        )

        # Always resolve PostScript names to CSS font families
        self._resolve_postscript_names(svg)

        if embed_fonts:
            self._insert_css_fontface(
                svg,
                subset_fonts=subset_fonts,
                font_format=font_format,
                use_data_uri=True,
            )

        if optimize:
            svg_utils.consolidate_defs(svg)

        with open(filepath, "w", encoding="utf-8") as f:
            svg_utils.write(svg, f, indent=indent)

    def rasterize(
        self, dpi: int = 0, rasterizer: BaseRasterizer | None = None
    ) -> Image.Image:
        """Rasterize the SVG document to PIL Image.

        Args:
            dpi: Dots per inch for rendering. If 0 (default), uses the
                rasterizer's default (96 DPI for ResvgRasterizer). Higher values
                produce larger, higher resolution images (e.g., 300 DPI for print
                quality). Only used if rasterizer is None.
            rasterizer: Optional custom rasterizer instance. If None, uses
                ResvgRasterizer with the specified dpi. Use this to specify
                alternative rasterizers like PlaywrightRasterizer for better
                SVG 2.0 feature support.

        Returns:
            PIL Image object in RGBA mode containing the rasterized SVG.

        Note:
            When using PlaywrightRasterizer, fonts are automatically embedded
            using local file:// URLs for optimal performance (60-80% faster
            than data URIs, 99% smaller SVG strings).

        Example:
            >>> # Default resvg rasterization
            >>> image = document.rasterize()

            >>> # High DPI rasterization
            >>> image = document.rasterize(dpi=300)

            >>> # Browser-based rasterization (fonts auto-embedded with file URLs)
            >>> from psd2svg.rasterizer import PlaywrightRasterizer
            >>> browser_rasterizer = PlaywrightRasterizer(dpi=96)
            >>> image = document.rasterize(rasterizer=browser_rasterizer)
        """
        if rasterizer is None:
            rasterizer = ResvgRasterizer(dpi=dpi)

        # Check if we need to auto-embed fonts for PlaywrightRasterizer
        # Import here to avoid circular dependency issues
        try:
            from psd2svg.rasterizer.playwright_rasterizer import PlaywrightRasterizer

            is_playwright = isinstance(rasterizer, PlaywrightRasterizer)
        except ImportError:
            is_playwright = False

        # NEW PATH: Auto-embed fonts for PlaywrightRasterizer with file:// URLs
        if is_playwright:
            # Create a deep copy to avoid modifying the original SVG
            svg = deepcopy(self.svg)

            # Embed images as data URIs (required for browser)
            nodes = svg.findall(".//image")
            if nodes:
                self._embed_images_as_data_uris(nodes, DEFAULT_IMAGE_FORMAT)

            # Always resolve PostScript names to CSS font families
            self._resolve_postscript_names(svg)

            # Embed fonts with file:// URLs (NEW)
            self._insert_css_fontface(
                svg,
                subset_fonts=False,  # No subsetting for file URLs (faster)
                font_format="ttf",  # Not used for file URLs
                use_data_uri=False,
            )

            # Convert to string and rasterize
            svg_str = svg_utils.tostring(svg, indent="  ")
            return rasterizer.from_string(svg_str)

        # ResvgRasterizer path: Pass font files directly via API
        if isinstance(rasterizer, ResvgRasterizer):
            svg_str = self.tostring(embed_images=True)
            # Extract font families from SVG and resolve to font files
            font_families = svg_utils.extract_font_families(self.svg)
            font_files = []
            for ps_name in font_families:
                _, resolved_font = self._resolve_postscript_to_family(ps_name)
                if resolved_font and resolved_font.file:
                    font_files.append(resolved_font.file)
            if font_files:
                return rasterizer.from_string(svg_str, font_files=font_files)
            else:
                return rasterizer.from_string(svg_str)

        # Default path: No fonts or other rasterizer
        svg_str = self.tostring(embed_images=True)
        return rasterizer.from_string(svg_str)

    def export(
        self,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
    ) -> dict[str, str | dict[str, bytes]]:
        """Export the SVG document in a serializable format.

        Note: Font information is now embedded in SVG font-family attributes,
        so no separate fonts list is exported.
        """
        return {
            "svg": svg_utils.tostring(self.svg, indent=indent),
            "images": {
                image_id: image_utils.encode_image(image, image_format)
                for image_id, image in self.images.items()
            },
        }

    @classmethod
    def load(
        cls,
        svg: str,
        images: dict[str, bytes],
        fonts: list[dict[str, str | float]] | None = None,
    ) -> "SVGDocument":
        """Load an SVGDocument from SVG content and image bytes.

        Args:
            svg: SVG content as a string.
            images: Dictionary mapping image IDs to image bytes.
            fonts: Deprecated parameter, ignored. Font information is now stored
                in SVG font-family attributes.
        """
        svg_node = ET.fromstring(svg)
        images_dict = {
            image_id: image_utils.decode_image(img_bytes)
            for image_id, img_bytes in images.items()
        }
        return SVGDocument(svg=svg_node, images=images_dict)

    def _resolve_postscript_to_family(
        self,
        postscript_name: str,
        charset_codepoints: set[int] | None = None,
    ) -> tuple[str, FontInfo | None]:
        """Resolve PostScript name to family name with charset-based matching.

        Attempts to resolve a PostScript font name to a font family name using:
        1. Static mapping (fast, 572 common fonts)
        2. System font resolution with optional charset matching

        Args:
            postscript_name: PostScript font name from PSD (e.g., "ArialMT", "Helvetica-Bold").
            charset_codepoints: Optional set of Unicode codepoints for charset-based matching.
                Improves font selection for multilingual text.

        Returns:
            Tuple of (family_name, resolved_font_info):
            - family_name: Font family name to use in font-family attribute.
                Falls back to PostScript name if resolution fails.
            - resolved_font_info: Resolved FontInfo with file path for embedding,
                or None if resolution failed.
        """
        # Try to find font metadata (static mapping first)
        try:
            font_info = FontInfo.find(postscript_name, charset_codepoints=charset_codepoints)
        except Exception as e:
            logger.debug(f"FontInfo.find() failed for {postscript_name}: {e}")
            # No mapping found - use PostScript name as-is
            return postscript_name, None

        if not font_info or not font_info.family:
            # No mapping found - use PostScript name as-is
            return postscript_name, None

        # Try to resolve to system font file (for embedding)
        try:
            resolved = font_info.resolve(charset_codepoints=charset_codepoints)
            if resolved and resolved.family:
                return resolved.family, resolved
        except Exception as e:
            logger.debug(f"FontInfo.resolve() failed for {postscript_name}: {e}")

        # Resolution failed but we have family name from static mapping
        return font_info.family, None

    def _handle_images(
        self,
        svg: ET.Element,
        embed_images: bool,
        image_prefix: str | None,
        image_format: str,
        svg_filepath: str | None = None,
    ) -> ET.Element:
        """Handle image embedding or saving.

        Modifies the provided SVG element in-place by updating <image> element
        href attributes to either data URIs or file paths.

        Args:
            svg: SVG element to modify in-place.
            embed_images: If True, embed images as base64 data URIs.
            image_prefix: Path prefix for saving images. If svg_filepath is provided,
                this is interpreted relative to the SVG file's directory.
            image_format: Image format to use when embedding or saving images.
            svg_filepath: Optional path to the SVG file. When provided, image_prefix
                is interpreted relative to this file's directory.

        Returns:
            The modified SVG element (same object as input).
        """
        nodes = svg.findall(".//image")

        # Validate that all image nodes have IDs and corresponding images exist
        for node in nodes:
            image_id = node.get("id")
            if image_id is None:
                raise RuntimeError(
                    f"<image> element missing required 'id' attribute: "
                    f"{ET.tostring(node, encoding='unicode')}"
                )
            if image_id not in self.images:
                raise RuntimeError(
                    f"No image found for <image> element with id='{image_id}'"
                )

        # Handle image resources (skip if no images).
        if len(nodes) == 0:
            return svg

        # image_prefix takes precedence over embed_images (as documented)
        if image_prefix is not None:
            self._save_images_to_files(nodes, image_prefix, image_format, svg_filepath)
        elif embed_images:
            self._embed_images_as_data_uris(nodes, image_format)
        else:
            raise ValueError(
                "Either embed_images must be True or image_prefix must be provided "
                "when the document contains images."
            )

        return svg

    def _embed_images_as_data_uris(
        self, nodes: list[ET.Element], image_format: str
    ) -> None:
        """Embed images as base64 data URIs in image nodes.

        Args:
            nodes: List of <image> elements to update.
            image_format: Image format to use for encoding.
        """
        for node in nodes:
            image_id = node.get("id")
            if image_id is None:
                raise RuntimeError("<image> element missing required 'id' attribute")
            if image_id not in self.images:
                raise RuntimeError(
                    f"No image found for <image> element with id='{image_id}'"
                )
            image = self.images[image_id]
            data_uri = image_utils.encode_data_uri(image, image_format)
            node.set("href", data_uri)

    def _save_images_to_files(
        self,
        nodes: list[ET.Element],
        image_prefix: str,
        image_format: str,
        svg_filepath: str | None,
    ) -> None:
        """Save images to files and update image nodes with file paths.

        Args:
            nodes: List of <image> elements to update.
            image_prefix: Path prefix for saving images.
            image_format: Image format to use for saving.
            svg_filepath: Optional path to the SVG file for relative path calculation.
        """
        # Determine base directory and filename prefix
        base_dir, prefix = self._resolve_image_output_paths(image_prefix, svg_filepath)

        # Create directory if needed
        if base_dir and not os.path.exists(base_dir):
            logger.debug("Creating directory: %s", base_dir)
            os.makedirs(base_dir)

        # Save each image and update node href
        for i, node in enumerate(nodes, start=1):
            image_id = node.get("id")
            if image_id is None:
                raise RuntimeError("<image> element missing required 'id' attribute")
            if image_id not in self.images:
                raise RuntimeError(
                    f"No image found for <image> element with id='{image_id}'"
                )

            image = self.images[image_id]
            filename = "{}{:02d}.{}".format(prefix, i, image_format.lower())
            filepath = os.path.join(base_dir, filename)

            # Save image (with JPEG conversion if needed)
            image_utils.save_image(image, filepath, image_format)

            # Set href: if svg_filepath provided, use relative path; otherwise use filename
            if svg_filepath:
                svg_dir = os.path.dirname(os.path.abspath(svg_filepath))
                href = os.path.relpath(filepath, svg_dir)
            else:
                href = filename
            node.set("href", href)

    def _resolve_image_output_paths(
        self, image_prefix: str, svg_filepath: str | None
    ) -> tuple[str, str]:
        """Resolve base directory and filename prefix for image output.

        Args:
            image_prefix: Path prefix for saving images.
            svg_filepath: Optional path to the SVG file for relative path calculation.

        Returns:
            Tuple of (base_dir, filename_prefix).

        Note:
            Special handling for "." prefix - treats it as "no prefix, just counter".
        """
        if svg_filepath:
            svg_dir = os.path.dirname(os.path.abspath(svg_filepath))
            # Special handling for "." - treat as "no prefix, just counter"
            if image_prefix == ".":
                return svg_dir, ""
            else:
                # image_prefix is relative to SVG file's directory
                base_dir = os.path.join(svg_dir, os.path.dirname(image_prefix))
                prefix = os.path.basename(image_prefix)
                return base_dir, prefix
        else:
            # No svg_filepath provided (tostring() case)
            # Special handling for "." - treat as "no prefix, just counter"
            if image_prefix == ".":
                return os.getcwd(), ""
            else:
                base_dir = os.path.dirname(image_prefix) or os.getcwd()
                prefix = os.path.basename(image_prefix)
                return base_dir, prefix

    def _extract_font_characters(
        self, svg: ET.Element, font_info: FontInfo
    ) -> set[str]:
        """Extract all characters used by a font in the SVG document.

        Args:
            svg: SVG element to search.
            font_info: Font information to match elements against.

        Returns:
            Set of characters used by this font, or empty set if none found.
        """
        # Step 1: Find elements using this font
        matching_elements = svg_utils.find_elements_with_font_family(
            svg, font_info.family
        )

        # Step 2: Extract characters from all matching elements
        chars_for_font: set[str] = set()
        if matching_elements:
            for element in matching_elements:
                text_content = svg_utils.extract_text_characters(element)
                if text_content:
                    chars_for_font.update(text_content)

            if chars_for_font:
                logger.debug(
                    f"Extracted {len(chars_for_font)} characters "
                    f"for font '{font_info.postscript_name}'"
                )

        return chars_for_font

    def _resolve_font_with_charset(
        self, font_info: FontInfo, chars: set[str]
    ) -> FontInfo | None:
        """Resolve font to system font file with optional charset matching.

        Args:
            font_info: Font information to resolve.
            chars: Characters used by this font (for charset-based matching).

        Returns:
            Resolved FontInfo with file path, or None if resolution failed.
        """
        # Create charset codepoints for font resolution
        charset_codepoints = None
        if chars:
            charset_codepoints = font_utils.create_charset_codepoints(chars)
            if charset_codepoints:
                logger.debug(
                    f"Using {len(charset_codepoints)} codepoints for "
                    f"charset-based resolution of '{font_info.postscript_name}'"
                )

        # Resolve font to system font file (with charset if available)
        resolved_font = font_info.resolve(charset_codepoints=charset_codepoints)
        if not resolved_font or not resolved_font.is_resolved():
            return None

        return resolved_font

    def _update_font_fallback_chains(
        self, svg: ET.Element, font_info: FontInfo, resolved_font: FontInfo
    ) -> None:
        """Update font-family attributes with fallback chains after substitution.

        Args:
            svg: SVG element to search and modify.
            font_info: Original font information.
            resolved_font: Resolved font information (may be different if substituted).
        """
        # Only update if substitution occurred
        if resolved_font.family == font_info.family:
            return

        # Find elements and add fallback chains
        matching_elements = svg_utils.find_elements_with_font_family(
            svg, font_info.family
        )
        if matching_elements:
            logger.info(
                f"Font fallback: '{font_info.family}' → '{resolved_font.family}'"
            )
            for element in matching_elements:
                svg_utils.add_font_family(element, resolved_font.family)

    def _resolve_postscript_names(self, svg: ET.Element) -> None:
        """Resolve PostScript names in SVG to CSS font family names.

        Scans SVG for elements with PostScript names in font-family attributes,
        resolves each to proper CSS family names, and updates font-family attributes.

        This method MUST be called for all SVG output (even when embed_fonts=False)
        to ensure PostScript names are converted to standard CSS font families.

        Args:
            svg: SVG element to search for font usage and update with family names.
        """
        # Get all unique PostScript names used in SVG
        postscript_names = svg_utils.extract_font_families(svg)

        for ps_name in postscript_names:
            # Step 1: Find elements using this PostScript name
            matching_elements = svg_utils.find_elements_with_font_family(svg, ps_name)
            if not matching_elements:
                continue

            # Step 2: Extract characters from these elements
            chars_for_font: set[str] = set()
            for element in matching_elements:
                text_content = svg_utils.extract_text_characters(element)
                if text_content:
                    chars_for_font.update(text_content)

            if chars_for_font:
                logger.debug(
                    f"Extracted {len(chars_for_font)} characters for PostScript font '{ps_name}'"
                )

            # Step 3: Resolve PostScript name → family name
            charset_codepoints = None
            if chars_for_font:
                charset_codepoints = font_utils.create_charset_codepoints(chars_for_font)
                if charset_codepoints:
                    logger.debug(
                        f"Using {len(charset_codepoints)} codepoints for "
                        f"charset-based resolution of '{ps_name}'"
                    )

            family_name, _ = self._resolve_postscript_to_family(
                ps_name, charset_codepoints
            )

            # Step 4: Update font-family attributes: PostScript → family
            if family_name != ps_name:
                # Font was resolved - update SVG elements
                logger.info(f"Font resolution: '{ps_name}' → '{family_name}'")
                for element in matching_elements:
                    # Replace PostScript name with CSS family name
                    svg_utils.replace_font_family(element, ps_name, family_name)
            else:
                # No resolution - keep PostScript name
                logger.debug(f"Keeping PostScript name '{ps_name}' (no resolution)")

    def _collect_resolved_fonts(
        self, svg: ET.Element
    ) -> list[tuple[FontInfo, set[str]]]:
        """Collect resolved fonts from SVG for CSS @font-face embedding.

        This method should be called AFTER _resolve_postscript_names() has updated
        font-family attributes to proper CSS family names.

        Args:
            svg: SVG element to search for font usage.

        Returns:
            List of (FontInfo, character set) tuples for embedding.
            Deduplicates fonts by file path.
        """
        resolved_fonts: dict[str, tuple[FontInfo, set[str]]] = {}

        # Get all font families from SVG (now resolved to CSS family names)
        font_families = svg_utils.extract_font_families(svg)

        for family_name in font_families:
            # Step 1: Find elements using this font family
            matching_elements = svg_utils.find_elements_with_font_family(
                svg, family_name
            )
            if not matching_elements:
                continue

            # Step 2: Extract characters from these elements
            chars_for_font: set[str] = set()
            for element in matching_elements:
                text_content = svg_utils.extract_text_characters(element)
                if text_content:
                    chars_for_font.update(text_content)

            # Step 3: Try to find and resolve font
            charset_codepoints = None
            if chars_for_font:
                charset_codepoints = font_utils.create_charset_codepoints(chars_for_font)

            try:
                font_info = FontInfo.find(family_name, charset_codepoints=charset_codepoints)
            except Exception as e:
                logger.debug(f"FontInfo.find() failed for {family_name}: {e}")
                continue

            if not font_info:
                logger.debug(f"No font info found for '{family_name}'")
                continue

            # Step 4: Resolve to system font file
            try:
                resolved_font = font_info.resolve(charset_codepoints=charset_codepoints)
            except Exception as e:
                logger.debug(f"Font resolution failed for '{family_name}': {e}")
                continue

            if not resolved_font or not resolved_font.file:
                logger.info(f"Cannot embed font '{family_name}': no file path available")
                continue

            # Step 5: Track for embedding (deduplicate by file path)
            file_key = resolved_font.file
            if file_key not in resolved_fonts:
                resolved_fonts[file_key] = (resolved_font, set())
            # Merge characters for the same font file
            resolved_fonts[file_key][1].update(chars_for_font)

        return list(resolved_fonts.values())

    def _generate_css_rules_for_fonts(
        self,
        resolved_fonts: list[tuple[FontInfo, set[str]]],
        subset_fonts: bool,
        font_format: str,
        use_data_uri: bool,
    ) -> list[str]:
        """Generate CSS @font-face rules from resolved fonts.

        Args:
            resolved_fonts: List of (FontInfo, character set) tuples.
            subset_fonts: If True, subset fonts (only applicable for data URIs).
            font_format: Font format for encoding (only applicable for data URIs).
            use_data_uri: If True, use data URIs; if False, use file:// URLs.

        Returns:
            List of CSS @font-face rule strings.
        """
        # Generate CSS rules from resolved fonts
        css_rules: list[str] = []
        source_desc = "data URI" if use_data_uri else "file:// URL"

        for resolved_font, chars_for_font in resolved_fonts:
            # Step 4: Generate CSS source (data URI or file URL)
            try:
                # Generate CSS source based on mode
                if use_data_uri:
                    # Prepare subset characters
                    subset_chars: set[str] = set()
                    if subset_fonts and chars_for_font:
                        subset_chars = chars_for_font
                    css_source = font_utils.encode_font_with_options(
                        font_path=resolved_font.file,
                        cache=self._font_data_cache,
                        subset_chars=subset_chars if subset_chars else None,
                        font_format=font_format,
                    )
                else:
                    css_source = font_utils.create_file_url(resolved_font.file)

                # Generate @font-face CSS rule
                css_rule = resolved_font.to_font_face_css(css_source)
                css_rules.append(css_rule)

                logger.debug(
                    f"Inserted CSS @font-face for '{resolved_font.family}' "
                    f"with {source_desc}: {css_source[:50]}..."
                )

            except (FileNotFoundError, IOError) as e:
                logger.warning(
                    f"Failed to create {source_desc} for font '{resolved_font.file}': {e}. "
                    "Font will not be embedded."
                )
                continue
            except Exception as e:
                logger.warning(
                    f"Failed to process font '{resolved_font.file}': {e}. "
                    "Font will not be embedded."
                )
                continue

        return css_rules

    def _insert_css_fontface(
        self,
        svg: ET.Element,
        subset_fonts: bool,
        font_format: str,
        use_data_uri: bool,
    ) -> None:
        """Insert CSS @font-face rules in a <style> element.

        This is the unified implementation for both data URI and file URL approaches.

        NOTE: This method should be called AFTER _resolve_postscript_names() has
        converted PostScript names to CSS font families in the SVG.

        Args:
            svg: SVG element to modify in-place (must have PostScript names resolved).
            subset_fonts: If True, subset fonts (only applicable for data URIs).
            font_format: Font format for encoding (only applicable for data URIs).
            use_data_uri: If True, use data URIs; if False, use file:// URLs.
        """
        # Collect resolved fonts for CSS embedding
        # (assumes PostScript names already resolved to CSS families)
        resolved_fonts = self._collect_resolved_fonts(svg)

        # Generate CSS rules
        css_rules = self._generate_css_rules_for_fonts(
            resolved_fonts, subset_fonts, font_format, use_data_uri
        )
        if not css_rules:
            logger.warning("No css font rules inserted; skipping <style> update")
            return

        # Insert all CSS rules into <style> element
        css_content = "\n".join(css_rules)
        svg_utils.insert_or_update_style_element(svg, css_content)


def convert(
    input_path: str,
    output_path: str,
    image_prefix: str | None = None,
    enable_text: bool = True,
    enable_live_shapes: bool = True,
    enable_title: bool = False,
    enable_class: bool = False,
    image_format: str = DEFAULT_IMAGE_FORMAT,
    text_letter_spacing_offset: float = 0.0,
    text_wrapping_mode: int = 0,
    font_mapping: dict[str, dict[str, float | str]] | None = None,
    embed_fonts: bool = False,
    font_format: str = "woff2",
) -> None:
    """Convenience method to convert a PSD file to an SVG file.

    Args:
        input_path: Path to the input PSD file.
        output_path: Path to the output SVG file.
        image_prefix: Optional path prefix to save extracted images. If None, images will be embedded.
        enable_text: Enable text layer conversion. If False, text layers are rasterized as images.
            Default is True.
        enable_live_shapes: Enable live shape conversion when possible. Disabling live shapes
            results in <path> elements instead of shape primitives like <rect> or <circle>.
            This may be more accurate, but less editable. Default is True.
        enable_title: Enable insertion of <title> elements with layer names.
            When False (default), title elements are omitted to reduce file size.
            Set to True to include <title> elements containing the Photoshop layer
            name for accessibility and debugging.
        enable_class: Enable insertion of class attributes on SVG elements for debugging
            purposes. When False (default), elements will not have class attributes,
            producing cleaner SVG output. Set to True to add class attributes for layer
            types, effects, and semantic roles (e.g., "shape-layer", "drop-shadow-effect",
            "fill") for debugging or styling.
        image_format: Image format to use when embedding or saving images.
            Supported formats: 'webp', 'png', 'jpeg'. Default is 'webp'.
        text_letter_spacing_offset: Global offset (in pixels) to add to all letter-spacing
            values. This can be used to compensate for differences between Photoshop's
            text rendering and SVG's text rendering. Typical values range from -0.02 to 0.02.
            Default is 0.0 (no offset).
        text_wrapping_mode: Text wrapping mode for bounding box text. Use 0 for no
            wrapping (default, native SVG <text>), or 1 for <foreignObject> with
            XHTML wrapping. Import TextWrappingMode from psd2svg.core.text for
            enum values. Only affects bounding box text (ShapeType=1); point text
            always uses native SVG <text> elements.
        font_mapping: Optional custom font mapping dictionary for resolving PostScript
            font names to font families without fontconfig. Useful on Windows or when
            fonts are not installed. Format:
            {"PostScriptName": {"family": str, "style": str, "weight": float}}.
            When not provided, uses built-in mapping for common fonts.
        embed_fonts: Enable font embedding in SVG. When True, fonts used in text layers
            are embedded as base64-encoded data URIs in @font-face rules. Default is False.
            Requires fontconfig on Linux/macOS for font file discovery.
        font_format: Font format for embedding. Supported formats: 'woff2' (best compression,
            default), 'woff', 'ttf', 'otf'. Only used when embed_fonts=True. WOFF2 provides
            90%+ size reduction through automatic font subsetting.
    """
    psdimage = PSDImage.open(input_path)
    document = SVGDocument.from_psd(
        psdimage,
        enable_text=enable_text,
        enable_live_shapes=enable_live_shapes,
        enable_title=enable_title,
        enable_class=enable_class,
        text_letter_spacing_offset=text_letter_spacing_offset,
        text_wrapping_mode=text_wrapping_mode,
        font_mapping=font_mapping,
    )
    document.save(
        output_path,
        embed_images=image_prefix is None,
        image_prefix=image_prefix,
        image_format=image_format,
        embed_fonts=embed_fonts,
        font_format=font_format,
    )
