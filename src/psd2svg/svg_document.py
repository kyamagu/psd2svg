import dataclasses
import logging
import os
import xml.etree.ElementTree as ET
from copy import deepcopy

from PIL import Image
from psd_tools import PSDImage

from psd2svg import image_utils, svg_utils
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
        svg_string = document.tostring(embed_images=True)

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
        Returns:
            SVGDocument object containing the converted SVG and images.
        """
        converter = Converter(
            psdimage,
            enable_live_shapes=enable_live_shapes,
            enable_text=enable_text,
            enable_title=enable_title,
            text_letter_spacing_offset=text_letter_spacing_offset,
        )
        converter.build()
        return SVGDocument(
            svg=converter.svg,
            images=converter.images,
            fonts=list(converter.fonts.values()),
        )

    def tostring(
        self,
        embed_images: bool = False,
        embed_fonts: bool = False,
        image_prefix: str | None = None,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
    ) -> str:
        """Convert SVG document to string.

        Args:
            embed_images: If True, embed images as base64 data URIs.
            embed_fonts: If True, embed fonts as @font-face rules in <style> element.
                WARNING: Font embedding may be subject to licensing restrictions.
                Ensure you have appropriate rights before distributing SVG files
                with embedded fonts.
            image_prefix: If provided, save images to files with this prefix.
            image_format: Image format to use when embedding or saving images.
            indent: Indentation string for pretty-printing the SVG.
        """
        svg = self._handle_images(
            embed_images, image_prefix, image_format, svg_filepath=None
        )

        if embed_fonts and self.fonts:
            self._embed_fonts(svg)

        return svg_utils.tostring(svg, indent=indent)

    def save(
        self,
        filepath: str,
        embed_images: bool = False,
        embed_fonts: bool = False,
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
            image_prefix: If provided, save images to files with this prefix
                relative to the output SVG file's directory.
            image_format: Image format to use when embedding or saving images.
            indent: Indentation string for pretty-printing the SVG.
        """
        svg = self._handle_images(
            embed_images, image_prefix, image_format, svg_filepath=filepath
        )

        if embed_fonts and self.fonts:
            self._embed_fonts(svg)

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

        # Handle image resources.
        if embed_images:
            for node, image in zip(nodes, self.images):
                data_uri = image_utils.encode_data_uri(image, image_format)
                node.set("href", data_uri)
        elif image_prefix is not None:
            # Determine the base directory for saving images
            if svg_filepath:
                svg_dir = os.path.dirname(os.path.abspath(svg_filepath))
                # Special handling for "." - treat as "no prefix, just counter"
                if image_prefix == ".":
                    base_dir = svg_dir
                    prefix = ""
                else:
                    # image_prefix is relative to SVG file's directory
                    base_dir = os.path.join(svg_dir, os.path.dirname(image_prefix))
                    prefix = os.path.basename(image_prefix)
            else:
                # No svg_filepath provided (tostring() case)
                # Special handling for "." - treat as "no prefix, just counter"
                if image_prefix == ".":
                    base_dir = os.getcwd()
                    prefix = ""
                else:
                    base_dir = os.path.dirname(image_prefix) or os.getcwd()
                    prefix = os.path.basename(image_prefix)

            # Create directory if needed
            if base_dir and not os.path.exists(base_dir):
                logger.debug("Creating directory: %s", base_dir)
                os.makedirs(base_dir)

            for i, (node, image) in enumerate(zip(nodes, self.images), start=1):
                # Construct filename: prefix + counter + extension
                filename = "{}{:02d}.{}".format(prefix, i, image_format.lower())
                filepath = os.path.join(base_dir, filename)

                # Convert RGBA to RGB for JPEG format (JPEG doesn't support alpha)
                if image_format.lower() == "jpeg" and image.mode == "RGBA":
                    # Create white background and paste image on it
                    rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3])  # Use alpha as mask
                    rgb_image.save(filepath)
                else:
                    image.save(filepath)

                # Set href: if svg_filepath provided, use relative path; otherwise use filename
                if svg_filepath:
                    svg_dir = os.path.dirname(os.path.abspath(svg_filepath))
                    href = os.path.relpath(filepath, svg_dir)
                else:
                    href = filename
                node.set("href", href)
        else:
            raise ValueError("Either embed must be True or path must be provided.")

        return svg

    def _embed_fonts(self, svg: ET.Element) -> None:
        """Embed fonts as @font-face rules in a <style> element.

        This modifies the provided SVG element in-place by inserting or updating
        a <style> element with @font-face CSS rules for all fonts in self.fonts.

        Args:
            svg: SVG element to modify.

        Warning:
            Font embedding may be subject to licensing restrictions. Ensure you
            have appropriate rights before distributing SVG files with embedded fonts.

        Note:
            - Caches encoded font data URIs to avoid re-encoding
            - Logs warnings for missing/unreadable fonts but continues
            - Creates <style> element as first child of <svg> root
            - Idempotent: calling multiple times won't duplicate fonts
        """
        if not self.fonts:
            return

        from psd2svg.core.font_utils import encode_font_data_uri

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
                # Use cache to avoid re-encoding
                if font_path not in self._font_data_cache:
                    logger.debug(f"Encoding font: {font_path}")
                    self._font_data_cache[font_path] = encode_font_data_uri(font_path)

                data_uri = self._font_data_cache[font_path]
                css_rule = font_info.to_font_face_css(data_uri)
                font_face_rules.append(css_rule)

            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Failed to embed font '{font_path}': {e}")
                continue

        if not font_face_rules:
            logger.warning("No fonts were successfully embedded")
            return

        # Create CSS content
        css_content = "\n".join(font_face_rules)

        # Find or create <style> element
        # Check if first child is already a <style> element with our fonts
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
            if "@font-face" in existing_text and css_content in existing_text:
                logger.debug("Fonts already embedded, skipping")
                return
            # Append to existing styles
            style_element.text = existing_text + "\n" + css_content
        else:
            # Create new style element as first child
            style_element = ET.Element("style")
            style_element.text = css_content
            svg.insert(0, style_element)

        logger.debug(f"Embedded {len(font_face_rules)} font(s) in <style> element")


def convert(
    input_path: str,
    output_path: str,
    image_prefix: str | None = None,
    enable_text: bool = True,
    enable_live_shapes: bool = True,
    enable_title: bool = True,
    image_format: str = DEFAULT_IMAGE_FORMAT,
    text_letter_spacing_offset: float = 0.0,
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
    """
    psdimage = PSDImage.open(input_path)
    document = SVGDocument.from_psd(
        psdimage,
        enable_text=enable_text,
        enable_live_shapes=enable_live_shapes,
        enable_title=enable_title,
        text_letter_spacing_offset=text_letter_spacing_offset,
    )
    document.save(
        output_path,
        embed_images=image_prefix is None,
        image_prefix=image_prefix,
        image_format=image_format,
    )
