import dataclasses
import logging
import os
import xml.etree.ElementTree as ET
from copy import deepcopy

from PIL import Image
from psd_tools import PSDImage

from psd2svg import font_subsetting, image_utils, svg_utils
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
        document.save("output.svg", embed_images=True)
        svg_string = document.tostring()  # Images embedded by default

        # Rasterize to PIL Image.
        rasterized = document.rasterize()

        # Export and load back.
        exported = document.export()
        document = SVGDocument.load(exported["svg"], exported["images"])
    """

    svg: ET.Element
    images: dict[str, Image.Image] = dataclasses.field(default_factory=dict)
    fonts: list[FontInfo] = dataclasses.field(default_factory=list)
    _font_data_cache: dict[str, str] = dataclasses.field(
        default_factory=dict, init=False, repr=False
    )
    _font_fallbacks: dict[str, str] = dataclasses.field(
        default_factory=dict, init=False, repr=False
    )
    _fonts_resolved: bool = dataclasses.field(default=False, init=False, repr=False)

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
        embed_images: bool = False,
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
            embed_images: If True, embed images as base64 data URIs.
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
            # Resolve fonts to get file paths (idempotent, safe to call multiple times)
            self._resolve_fonts()
            font_files = [info.file for info in self.fonts if info.file]
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

    def _resolve_fonts(self) -> None:
        """Resolve fonts and populate fallback mappings.

        This method:
        1. Resolves each font in self.fonts to actual system fonts
        2. Replaces fonts in self.fonts with resolved versions (for embedding)
        3. Populates self._font_fallbacks with substitution mappings

        Note: Does NOT modify the SVG tree. Call _update_svg_font_fallbacks()
        separately to update a specific SVG tree with fallback chains.

        Called before font embedding (only when embed_fonts=True).
        Idempotent - can be called multiple times safely.
        """
        # Skip if already resolved
        if self._fonts_resolved:
            return

        # Resolve fonts and update the font list
        resolved_fonts = []
        for font_info in self.fonts:
            resolved = font_info.resolve()
            if resolved:
                # Track substitution for fallback chain generation
                if resolved.family != font_info.family:
                    self._font_fallbacks[font_info.family] = resolved.family
                    logger.info(
                        f"Font fallback: '{font_info.family}' → '{resolved.family}'"
                    )
                # Use resolved font (has file path)
                resolved_fonts.append(resolved)
            else:
                # Keep original if resolution fails
                resolved_fonts.append(font_info)

        # Replace font list with resolved versions
        self.fonts = resolved_fonts

        # Mark as resolved
        self._fonts_resolved = True

    def _update_svg_font_fallbacks(self, svg: ET.Element) -> None:
        """Update SVG text elements with font fallback chains.

        Traverses the SVG tree and updates font-family attributes to include
        fallback fonts for any substituted fonts.

        Args:
            svg: SVG element tree to update (typically a copy, not the original).
        """
        for element in svg.iter():
            # Check font-family attribute
            font_family = element.get("font-family")
            if font_family:
                updated = self._add_fallback_to_font_family(font_family)
                if updated != font_family:
                    element.set("font-family", updated)

            # Check style attribute for font-family
            style = element.get("style")
            if style and "font-family:" in style:
                updated_style = self._add_fallback_to_style(style)
                if updated_style != style:
                    element.set("style", updated_style)

    def _add_fallback_to_font_family(self, font_family: str) -> str:
        """Add fallback to a font-family value.

        Args:
            font_family: Original font family (e.g., "'Arial'")

        Returns:
            Updated font family with fallback (e.g., "'Arial', 'DejaVu Sans'")
        """
        # Strip quotes to get clean family name
        clean_family = font_family.strip("'\"")

        # Check if substitution exists
        if clean_family in self._font_fallbacks:
            fallback = self._font_fallbacks[clean_family]
            return f"'{clean_family}', '{fallback}'"

        return font_family

    def _add_fallback_to_style(self, style: str) -> str:
        """Add fallback to font-family in a style attribute.

        Args:
            style: Style attribute value (e.g., "font-family: 'Arial'; color: red")

        Returns:
            Updated style with fallback in font-family
        """
        import re

        def replace_font_family(match: re.Match[str]) -> str:
            font_family_value = match.group(1).strip()
            # Parse the first font (requested font)
            # Font family values can be like: 'Arial' or Arial or "Arial"
            families = [f.strip().strip("'\"") for f in font_family_value.split(",")]
            if families and families[0] in self._font_fallbacks:
                fallback = self._font_fallbacks[families[0]]
                # Build fallback chain
                return f"font-family: '{families[0]}', '{fallback}'"
            return match.group(0)

        # Replace font-family in style attribute
        return re.sub(r"font-family:\s*([^;]+)", replace_font_family, style)

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

        # Resolve fonts before embedding (queries fontconfig if needed)
        # This modifies self.fonts and self._font_fallbacks but NOT the SVG tree
        self._resolve_fonts()

        # Update this SVG copy with font fallback chains (if any substitutions occurred)
        if self._font_fallbacks:
            self._update_svg_font_fallbacks(svg)

        # Extract Unicode usage if subsetting is enabled
        font_usage: dict[str, set[str]] = {}
        if subset_fonts:
            try:
                font_usage = font_subsetting.get_font_usage_from_svg(svg)
            except ImportError as e:
                logger.warning(
                    f"Font subsetting disabled: {e}. "
                    "Fonts will be embedded without subsetting."
                )
                subset_fonts = False  # Disable subsetting for this call

        # Generate @font-face CSS rules
        font_face_rules = self._generate_font_face_rules(
            font_usage, subset_fonts, font_format
        )

        if not font_face_rules:
            logger.warning("No fonts were successfully embedded")
            return

        # Create CSS content and insert into SVG
        css_content = "\n".join(font_face_rules)
        self._insert_or_update_style_element(svg, css_content)

        logger.debug(f"Embedded {len(font_face_rules)} font(s) in <style> element")

    def _generate_font_face_rules(
        self,
        font_usage: dict[str, set[str]],
        subset_fonts: bool,
        font_format: str,
    ) -> list[str]:
        """Generate @font-face CSS rules for all fonts.

        Args:
            font_usage: Dictionary mapping font families to character sets.
                Empty dict if subsetting is disabled.
            subset_fonts: Whether to subset fonts.
            font_format: Font format for embedding ("ttf", "otf", "woff2").

        Returns:
            List of @font-face CSS rule strings.

        Note:
            - Uses self._font_data_cache for caching encoded fonts
            - Skips duplicate fonts (same file path)
            - Logs warnings for missing/unreadable fonts but continues
        """
        font_face_rules = []
        seen_fonts = set()  # Track fonts by file path to avoid duplicates

        for font_info in self.fonts:
            # Skip fonts that haven't been resolved to system font files
            # Note: _resolve_fonts() has already resolved fonts
            if not font_info.is_resolved():
                logger.info(
                    f"Cannot embed font '{font_info.postscript_name}': "
                    "no file path available"
                )
                continue

            # Skip duplicates (fonts with same file path)
            font_path = font_info.file
            if font_path in seen_fonts:
                continue
            seen_fonts.add(font_path)

            # Generate CSS rule for this font
            css_rule = self._generate_single_font_face_rule(
                font_info, font_usage, subset_fonts, font_format
            )
            if css_rule:
                font_face_rules.append(css_rule)

        return font_face_rules

    def _generate_single_font_face_rule(
        self,
        font_info: FontInfo,
        font_usage: dict[str, set[str]],
        subset_fonts: bool,
        font_format: str,
    ) -> str | None:
        """Generate a single @font-face CSS rule for a font.

        Args:
            font_info: Font information.
            font_usage: Dictionary mapping font families to character sets.
            subset_fonts: Whether to subset fonts.
            font_format: Font format for embedding ("ttf", "otf", "woff2").

        Returns:
            CSS @font-face rule string, or None if font processing failed.

        Note:
            - Logs warnings for non-critical errors and returns None
            - Re-raises ImportError for missing dependencies
            - FontInfo should already be resolved with file path populated
        """
        # Check if font has been resolved to a system font file
        # Note: _resolve_fonts() has already resolved fonts
        if not font_info.is_resolved():
            raise ValueError(
                f"Cannot embed font '{font_info.postscript_name}': "
                "no file path available"
            )

        font_path = font_info.file

        try:
            # Get subset characters for this font (if subsetting enabled)
            subset_chars = font_usage.get(font_info.family) if subset_fonts else None

            # Handle missing characters in subsetting mode
            if subset_fonts and not subset_chars:
                logger.warning(
                    f"No characters found for font '{font_info.family}', "
                    "using full font"
                )
                subset_chars = None

            # Encode font with caching
            data_uri = font_utils.encode_font_with_options(
                font_path=font_path,
                cache=self._font_data_cache,
                subset_chars=subset_chars,
                font_format=font_format,
            )

            # Generate CSS rule
            return font_info.to_font_face_css(data_uri)

        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Failed to embed font '{font_path}': {e}")
            return None
        except ImportError as e:
            logger.error(f"Font subsetting failed (missing dependency): {e}")
            raise
        except Exception as e:
            logger.warning(f"Failed to process font '{font_path}': {e}")
            return None

    def _insert_or_update_style_element(
        self, svg: ET.Element, css_content: str
    ) -> None:
        """Insert or update a <style> element in the SVG root.

        Args:
            svg: SVG root element to modify.
            css_content: CSS content to insert or append.

        Note:
            - If a <style> element exists as first child, appends to it
            - Otherwise creates a new <style> element as first child
            - Idempotent: skips if CSS content already present
        """
        # Find existing <style> element (check first child only)
        style_element = None
        if len(svg) > 0:
            first_child = svg[0]
            # Check if it's a style element (handle namespaced tags)
            tag = first_child.tag
            local_name = tag.split("}")[-1] if "}" in tag else tag
            if local_name == "style":
                style_element = first_child

        if style_element is not None:
            # Update existing style element
            existing_text = style_element.text or ""
            # Check if our fonts are already embedded (idempotent check)
            if css_content in existing_text:
                logger.debug("CSS content already present, skipping")
                return
            # Append to existing styles
            style_element.text = existing_text + "\n" + css_content
        else:
            # Create new style element as first child
            style_element = ET.Element("style")
            style_element.text = css_content
            svg.insert(0, style_element)

    def optimize(self, consolidate_defs: bool = True) -> None:
        """Optimize SVG structure in-place.

        This method applies optimizations to improve SVG structure,
        file size, and rendering performance. All optimizations modify the
        SVG element tree directly.

        Args:
            consolidate_defs: Merge all <defs> elements and move definition
                elements (filters, gradients, patterns, etc.) into a global
                <defs> at the beginning of the SVG document. This improves
                document structure and follows SVG best practices. Default: True.

        Example:
            >>> document = SVGDocument.from_psd(psdimage)
            >>> document.optimize()  # Apply default optimizations
            >>> document.save('output.svg')

            >>> # Disable optimization
            >>> document.optimize(consolidate_defs=False)

        Note:
            Additional optimizations (deduplication, ID minification, unused
            removal) may be added in future versions.
        """
        if consolidate_defs:
            svg_utils.consolidate_defs(self.svg)


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
