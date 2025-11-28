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
        document.save("output.svg", embed_images=True)
        svg_string = document.tostring()  # Images embedded by default

        # Rasterize to PIL Image.
        rasterized = document.rasterize()

        # Export and load back.
        exported = document.export()
        document = SVGDocument.load(exported["svg"], exported["images"])
    """

    svg: ET.Element
    images: list[Image.Image] = dataclasses.field(default_factory=list)
    fonts: list[FontInfo] = dataclasses.field(default_factory=list)
    _font_data_cache: dict[str, str] = dataclasses.field(
        default_factory=dict, init=False, repr=False
    )

    @staticmethod
    def from_psd(
        psdimage: PSDImage,
        enable_live_shapes: bool = True,
        enable_text: bool = True,
        enable_title: bool = True,
        text_letter_spacing_offset: float = 0.0,
        text_wrapping_mode: int = 0,
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
                When True (default), each layer in the SVG will have a <title>
                element containing the Photoshop layer name for accessibility and
                debugging. Set to False to omit title elements and reduce file size.
            text_letter_spacing_offset: Global offset (in pixels) to add to all
                letter-spacing values. This can be used to compensate for differences
                between Photoshop's text rendering and SVG's text rendering. Typical
                values range from -0.02 to 0.02. Default is 0.0 (no offset).
            text_wrapping_mode: Text wrapping mode for bounding box text. Use 0 for no
                wrapping (default, native SVG <text>), or 1 for <foreignObject> with
                XHTML wrapping. Import TextWrappingMode from psd2svg.core.text for
                enum values. Only affects bounding box text (ShapeType=1); point text
                always uses native SVG <text> elements.
        Returns:
            SVGDocument object containing the converted SVG and images.
        """
        converter = Converter(
            psdimage,
            enable_live_shapes=enable_live_shapes,
            enable_text=enable_text,
            enable_title=enable_title,
            text_letter_spacing_offset=text_letter_spacing_offset,
            text_wrapping_mode=text_wrapping_mode,
        )
        converter.build()
        return SVGDocument(
            svg=converter.svg,
            images=converter.images,
            fonts=list(converter.fonts.values()),
        )

    def tostring(
        self,
        embed_images: bool = True,
        embed_fonts: bool = False,
        subset_fonts: bool = False,
        font_format: str = "ttf",
        image_prefix: str | None = None,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
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
                90%+ reduction).
            font_format: Font format for embedding: "ttf" (default), "otf", or "woff2".
                WOFF2 provides best compression and automatically enables subsetting.
            image_prefix: If provided, save images to files with this prefix.
                When specified, embed_images is ignored.
            image_format: Image format to use when embedding or saving images.
            indent: Indentation string for pretty-printing the SVG.
        """
        # Validate font subsetting parameters
        if subset_fonts and not embed_fonts:
            raise ValueError("subset_fonts=True requires embed_fonts=True")

        # Auto-enable subsetting for WOFF2 (web-optimized format)
        if font_format == "woff2" and embed_fonts:
            subset_fonts = True

        svg = self._handle_images(
            embed_images, image_prefix, image_format, svg_filepath=None
        )

        if embed_fonts and self.fonts:
            self._embed_fonts(svg, subset_fonts=subset_fonts, font_format=font_format)

        return svg_utils.tostring(svg, indent=indent)

    def save(
        self,
        filepath: str,
        embed_images: bool = False,
        embed_fonts: bool = False,
        subset_fonts: bool = False,
        font_format: str = "ttf",
        image_prefix: str | None = None,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
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
                90%+ reduction).
            font_format: Font format for embedding: "ttf" (default), "otf", or "woff2".
                WOFF2 provides best compression and automatically enables subsetting.
            image_prefix: If provided, save images to files with this prefix
                relative to the output SVG file's directory.
            image_format: Image format to use when embedding or saving images.
            indent: Indentation string for pretty-printing the SVG.
        """
        # Validate font subsetting parameters
        if subset_fonts and not embed_fonts:
            raise ValueError("subset_fonts=True requires embed_fonts=True")

        # Auto-enable subsetting for WOFF2 (web-optimized format)
        if font_format == "woff2" and embed_fonts:
            subset_fonts = True

        svg = self._handle_images(
            embed_images, image_prefix, image_format, svg_filepath=filepath
        )

        if embed_fonts and self.fonts:
            self._embed_fonts(svg, subset_fonts=subset_fonts, font_format=font_format)

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
            font_files = [info.file for info in self.fonts]
            return rasterizer.from_string(svg, font_files=font_files)

        return rasterizer.from_string(svg)

    def export(
        self,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
    ) -> dict[str, str | list[bytes] | list[dict[str, str | float]]]:
        """Export the SVG document in a serializable format."""
        return {
            "svg": svg_utils.tostring(self.svg, indent=indent),
            "images": [
                image_utils.encode_image(image, image_format) for image in self.images
            ],
            "fonts": [font_info.to_dict() for font_info in self.fonts],
        }

    @classmethod
    def load(
        cls,
        svg: str,
        images: list[bytes],
        fonts: list[dict[str, str | float]] | None = None,
    ) -> "SVGDocument":
        """Load an SVGDocument from SVG content and image bytes.

        Args:
            svg: SVG content as a string.
            images: List of image bytes corresponding to <image> nodes in the SVG.
            fonts: Optional list of font information dictionaries.
        """
        svg_node = ET.fromstring(svg)
        pil_images = [image_utils.decode_image(img_bytes) for img_bytes in images]
        font_infos = (
            [FontInfo.from_dict(font_dict) for font_dict in fonts] if fonts else []
        )
        return SVGDocument(svg=svg_node, images=pil_images, fonts=font_infos)

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
        if len(nodes) != len(self.images):
            raise RuntimeError("Number of <image> nodes and images do not match.")

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
        for node, image in zip(nodes, self.images):
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
        for i, (node, image) in enumerate(zip(nodes, self.images), start=1):
            filename = "{}{:02d}.{}".format(prefix, i, image_format.lower())
            filepath = os.path.join(base_dir, filename)

            # Save image (with JPEG conversion if needed)
            self._save_image_file(image, filepath, image_format)

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

    def _save_image_file(
        self, image: Image.Image, filepath: str, image_format: str
    ) -> None:
        """Save a PIL Image to file, with JPEG conversion if needed.

        Args:
            image: PIL Image to save.
            filepath: Output file path.
            image_format: Image format (used for JPEG RGBA conversion).

        Note:
            JPEG doesn't support alpha channel, so RGBA images are converted
            to RGB with a white background.
        """
        if image_format.lower() == "jpeg" and image.mode == "RGBA":
            # Create white background and paste image on it
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha as mask
            rgb_image.save(filepath)
        else:
            image.save(filepath)

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

        # Extract Unicode usage if subsetting is enabled
        font_usage: dict[str, set[str]] = {}
        if subset_fonts:
            try:
                from psd2svg import font_subsetting

                font_usage = font_subsetting.extract_used_unicode(svg)
                logger.debug(
                    f"Extracted {len(font_usage)} font(s) with "
                    f"{sum(len(chars) for chars in font_usage.values())} unique char(s)"
                )
            except ImportError as e:
                logger.error(
                    f"Font subsetting requires fonttools package: {e}. "
                    "Install with: uv sync --group fonts"
                )
                raise

        # Collect @font-face rules
        font_face_rules = []
        seen_fonts = set()  # Track fonts by file path to avoid duplicates

        for font_info in self.fonts:
            font_path = font_info.file

            # Skip duplicates
            if font_path in seen_fonts:
                continue
            seen_fonts.add(font_path)

            try:
                if subset_fonts:
                    # Subset and convert font
                    from psd2svg import font_subsetting

                    # Get characters used by this specific font family
                    chars = font_usage.get(font_info.family, set())

                    if not chars:
                        logger.warning(
                            f"No characters found for font '{font_info.family}', "
                            "skipping subsetting"
                        )
                        # Fall back to full font encoding
                        if font_path not in self._font_data_cache:
                            logger.debug(f"Encoding full font: {font_path}")
                            self._font_data_cache[font_path] = (
                                font_utils.encode_font_data_uri(font_path)
                            )
                        data_uri = self._font_data_cache[font_path]
                    else:
                        # Create cache key for subset fonts (include format and chars)
                        cache_key = f"{font_path}:{font_format}:{len(chars)}"

                        if cache_key not in self._font_data_cache:
                            logger.debug(
                                f"Subsetting font: {font_path} -> {font_format} "
                                f"({len(chars)} chars)"
                            )
                            font_bytes = font_subsetting.subset_font(
                                input_path=font_path,
                                output_format=font_format,
                                unicode_chars=chars,
                            )
                            data_uri = font_utils.encode_font_bytes_to_data_uri(
                                font_bytes, font_format
                            )
                            self._font_data_cache[cache_key] = data_uri
                        else:
                            data_uri = self._font_data_cache[cache_key]
                else:
                    # Use full font encoding (original behavior)
                    if font_path not in self._font_data_cache:
                        logger.debug(f"Encoding font: {font_path}")
                        self._font_data_cache[font_path] = (
                            font_utils.encode_font_data_uri(font_path)
                        )

                    data_uri = self._font_data_cache[font_path]

                css_rule = font_info.to_font_face_css(data_uri)
                font_face_rules.append(css_rule)

            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Failed to embed font '{font_path}': {e}")
                continue
            except ImportError as e:
                logger.error(f"Font subsetting failed (missing dependency): {e}")
                raise
            except Exception as e:
                logger.warning(f"Failed to subset font '{font_path}': {e}")
                continue

        if not font_face_rules:
            logger.warning("No fonts were successfully embedded")
            return

        # Create CSS content
        css_content = "\n".join(font_face_rules)

        # Insert or update <style> element with CSS content
        self._insert_or_update_style_element(svg, css_content)

        logger.debug(f"Embedded {len(font_face_rules)} font(s) in <style> element")

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


def convert(
    input_path: str,
    output_path: str,
    image_prefix: str | None = None,
    enable_text: bool = True,
    enable_live_shapes: bool = True,
    enable_title: bool = True,
    image_format: str = DEFAULT_IMAGE_FORMAT,
    text_letter_spacing_offset: float = 0.0,
    text_wrapping_mode: int = 0,
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
            When True (default), each layer in the SVG will have a <title> element
            containing the Photoshop layer name for accessibility and debugging.
            Set to False to omit title elements and reduce file size.
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
    """
    psdimage = PSDImage.open(input_path)
    document = SVGDocument.from_psd(
        psdimage,
        enable_text=enable_text,
        enable_live_shapes=enable_live_shapes,
        enable_title=enable_title,
        text_letter_spacing_offset=text_letter_spacing_offset,
        text_wrapping_mode=text_wrapping_mode,
    )
    document.save(
        output_path,
        embed_images=image_prefix is None,
        image_prefix=image_prefix,
        image_format=image_format,
    )
