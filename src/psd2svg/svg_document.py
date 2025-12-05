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
        document = SVGDocument.load(exported["svg"], exported["images"], exported["fonts"])
    """

    svg: ET.Element
    images: dict[str, Image.Image] = dataclasses.field(default_factory=dict)
    fonts: list[FontInfo] = dataclasses.field(default_factory=list)
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
            fonts=list(converter.fonts.values()),
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
        svg = self._handle_images(
            embed_images, image_prefix, image_format, svg_filepath=None
        )

        if embed_fonts and self.fonts:
            self._embed_fonts(svg, subset_fonts=subset_fonts, font_format=font_format)

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
        svg = self._handle_images(
            embed_images, image_prefix, image_format, svg_filepath=filepath
        )

        if embed_fonts and self.fonts:
            self._embed_fonts(svg, subset_fonts=subset_fonts, font_format=font_format)

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
            in the SVG content to ensure correct rendering in the browser.

        Example:
            >>> # Default resvg rasterization
            >>> image = document.rasterize()

            >>> # High DPI rasterization
            >>> image = document.rasterize(dpi=300)

            >>> # Browser-based rasterization (fonts auto-embedded)
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

        # Auto-embed fonts for PlaywrightRasterizer
        if is_playwright and self.fonts:
            svg = self.tostring(embed_images=True, embed_fonts=True)
        else:
            svg = self.tostring(embed_images=True)

        # Font files are only supported by ResvgRasterizer
        if isinstance(rasterizer, ResvgRasterizer) and self.fonts:
            # Resolve fonts to get file paths
            font_files = []
            for font_info in self.fonts:
                resolved = font_info.resolve()
                if resolved and resolved.file:
                    font_files.append(resolved.file)
            return rasterizer.from_string(svg, font_files=font_files)

        return rasterizer.from_string(svg)

    def export(
        self,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
    ) -> dict[str, str | dict[str, bytes] | list[dict[str, str | float]]]:
        """Export the SVG document in a serializable format."""
        return {
            "svg": svg_utils.tostring(self.svg, indent=indent),
            "images": {
                image_id: image_utils.encode_image(image, image_format)
                for image_id, image in self.images.items()
            },
            "fonts": [font_info.to_dict() for font_info in self.fonts],
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
            fonts: Optional list of font information dictionaries.
        """
        svg_node = ET.fromstring(svg)
        images_dict = {
            image_id: image_utils.decode_image(img_bytes)
            for image_id, img_bytes in images.items()
        }
        font_infos = (
            [FontInfo.from_dict(font_dict) for font_dict in fonts] if fonts else []
        )
        return SVGDocument(svg=svg_node, images=images_dict, fonts=font_infos)

    def _extract_characters_from_elements(self, elements: list[ET.Element]) -> set[str]:
        """Extract unique characters used in the given text elements.

        Args:
            elements: List of text/tspan elements to extract characters from.

        Returns:
            Set of unique Unicode characters found in the elements.

        Note:
            - Extracts direct text content only (element.text, not children)
            - Does NOT include tail (content after element's closing tag)
            - Decodes XML entities (e.g., &lt;, &#x4E00;)
        """
        import html

        characters: set[str] = set()

        for element in elements:
            # Extract direct text content (element.text only, not children or tail)
            if element.text:
                text_content = html.unescape(element.text)
                characters.update(text_content)

        return characters

    def _handle_images(
        self,
        embed_images: bool,
        image_prefix: str | None,
        image_format: str,
        svg_filepath: str | None = None,
    ) -> ET.Element:
        """Handle image embedding or saving.

        Args:
            embed_images: If True, embed images as base64 data URIs.
            image_prefix: Path prefix for saving images. If svg_filepath is provided,
                this is interpreted relative to the SVG file's directory.
            image_format: Image format to use when embedding or saving images.
            svg_filepath: Optional path to the SVG file. When provided, image_prefix
                is interpreted relative to this file's directory.
        """
        svg = deepcopy(self.svg)  # Avoid modifying the original SVG.
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

    def _process_single_font(
        self,
        font_info: FontInfo,
        svg: ET.Element,
        subset_enabled: bool,
        font_format: str,
    ) -> str | None:
        """Process a single font: resolve, update fallbacks, subset, and generate CSS.

        This method performs all font processing steps for a single font:
        1. Find text/tspan elements using this font
        2. Resolve font to system font file (fontconfig/Windows registry)
        3. Update matched elements with fallback chains if substitution occurred
        4. Extract subset characters from matched elements (if subsetting enabled)
        5. Generate @font-face CSS rule with encoded font data

        Args:
            font_info: Font to process.
            svg: SVG element tree to search and update.
            subset_enabled: Whether font subsetting is enabled.
            font_format: Font format for embedding ("ttf", "otf", "woff2").

        Returns:
            CSS @font-face rule string, or None if font processing failed.

        Note:
            - Modifies SVG tree in-place (adds fallback chains)
            - Uses self._font_data_cache for caching
            - Logs warnings for errors but continues gracefully
        """
        # Step 1: Find elements using this font
        matching_elements = svg_utils.find_elements_with_font_family(
            svg, font_info.family
        )

        # Step 2: Resolve font to system font file
        resolved_font = font_info.resolve()
        if not resolved_font or not resolved_font.is_resolved():
            logger.info(
                f"Cannot embed font '{font_info.postscript_name}': "
                "no file path available"
            )
            return None

        # Step 3: Update fallbacks if substitution occurred (only if elements found)
        if matching_elements and resolved_font.family != font_info.family:
            logger.info(
                f"Font fallback: '{font_info.family}' → '{resolved_font.family}'"
            )
            # Add fallback chain to matched elements
            for element in matching_elements:
                svg_utils.add_font_family(
                    element, font_info.family, resolved_font.family
                )

        # Step 4: Extract subset characters (if enabled and elements found)
        subset_chars: set[str] | None = None
        if subset_enabled and matching_elements:
            subset_chars = self._extract_characters_from_elements(matching_elements)
            if not subset_chars:
                logger.warning(
                    f"No characters found for font '{font_info.family}', "
                    "using full font"
                )
                subset_chars = None

        # Step 5: Generate CSS rule with font encoding
        font_path = resolved_font.file
        try:
            # Encode font with caching
            data_uri = font_utils.encode_font_with_options(
                font_path=font_path,
                cache=self._font_data_cache,
                subset_chars=subset_chars,
                font_format=font_format,
            )

            # Generate CSS rule
            return resolved_font.to_font_face_css(data_uri)

        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Failed to embed font '{font_path}': {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to process font '{font_path}': {e}")
            return None

    def _embed_fonts(
        self, svg: ET.Element, subset_fonts: bool = False, font_format: str = "ttf"
    ) -> None:
        """Embed fonts as @font-face rules in a <style> element.

        This modifies the provided SVG element in-place by inserting or updating
        a <style> element with @font-face CSS rules for all fonts in self.fonts.

        Args:
            svg: SVG element to modify.
            subset_fonts: If True, subset fonts to only include glyphs used in the SVG.
            font_format: Font format for embedding: "ttf" (default), "otf", or "woff2".

        Warning:
            Font embedding may be subject to licensing restrictions. Ensure you
            have appropriate rights before distributing SVG files with embedded fonts.

        Note:
            - Caches encoded font data URIs to avoid re-encoding
            - Logs warnings for missing/unreadable fonts but continues
            - Creates <style> element as first child of <svg> root
            - Idempotent: calling multiple times won't duplicate fonts
            - Font subsetting requires fonttools package (uv sync --group fonts)
        """
        if not self.fonts:
            return

        # Collect CSS rules by processing each font independently
        css_rules: list[str] = []
        seen_fonts: set[str] = set()  # Track fonts by file path to avoid duplicates

        for font_info in self.fonts:
            # Process this font: resolve, update fallbacks, subset, generate CSS
            css_rule = self._process_single_font(
                font_info=font_info,
                svg=svg,
                subset_enabled=subset_fonts,
                font_format=font_format,
            )

            if css_rule:
                # Skip duplicates (fonts with same file path)
                # Note: resolved font might have different path than original
                resolved = font_info.resolve()
                if resolved and resolved.file:
                    font_path = resolved.file
                    if font_path not in seen_fonts:
                        seen_fonts.add(font_path)
                        css_rules.append(css_rule)

        if not css_rules:
            logger.warning("No fonts were successfully embedded")
            return

        # Insert all CSS rules into <style> element
        css_content = "\n".join(css_rules)
        svg_utils.insert_or_update_style_element(svg, css_content)

        logger.debug(f"Embedded {len(css_rules)} font(s) in <style> element")


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
