import dataclasses
import logging
import os
import xml.etree.ElementTree as ET
from copy import deepcopy

from PIL import Image
from psd_tools import PSDImage

from psd2svg import image_utils, svg_utils
from psd2svg.core.converter import Converter
from psd2svg.rasterizer import ResvgRasterizer

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_FORMAT = "webp"


@dataclasses.dataclass
class SVGDocument:
    """SVG document and resources.

    Example usage:

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
    # TODO: Font handling.

    @staticmethod
    def from_psd(psdimage: PSDImage) -> "SVGDocument":
        """Create a new SVGDocument from a PSDImage.

        Args:
            psdimage: PSDImage object to convert.
        """
        converter = Converter(psdimage)
        converter.build()
        return SVGDocument(svg=converter.svg, images=converter.images)

    def tostring(
        self,
        embed_images: bool = False,
        image_prefix: str | None = None,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
    ) -> str:
        """Embed images as base64 data URIs.

        Args:
            embed_images: If True, embed images as base64 data URIs.
            image_prefix: If provided, save images to files with this prefix.
            image_format: Image format to use when embedding or saving images.
            indent: Indentation string for pretty-printing the SVG.
        """
        svg = self._handle_images(embed_images, image_prefix, image_format)
        return svg_utils.tostring(svg, indent=indent)

    def save(
        self,
        filepath: str,
        embed_images: bool = False,
        image_prefix: str | None = None,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
    ) -> None:
        """Save the SVG to a file.

        Args:
            filepath: Path to the output SVG file.
            embed_images: If True, embed images as base64 data URIs.
            image_prefix: If provided, save images to files with this prefix.
            image_format: Image format to use when embedding or saving images.
            indent: Indentation string for pretty-printing the SVG.
        """
        svg = self._handle_images(embed_images, image_prefix, image_format)
        with open(filepath, "w", encoding="utf-8") as f:
            svg_utils.write(svg, f, indent=indent)

    def rasterize(self, dpi: int = 0) -> Image.Image:
        """Rasterize the SVG document to PIL Image using resvg.

        Args:
            dpi: Dots per inch for rendering. If 0 (default), uses resvg's
                default of 96 DPI. Higher values produce larger, higher
                resolution images (e.g., 300 DPI for print quality).

        Returns:
            PIL Image object in RGBA mode containing the rasterized SVG.
        """
        rasterizer = ResvgRasterizer(dpi=dpi)
        svg = self.tostring(embed_images=True)
        return rasterizer.from_string(svg)

    def export(
        self,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        indent: str = "  ",
    ) -> dict[str, str | list[bytes]]:
        """Export the SVG document in a serializable format."""
        return {
            "svg": svg_utils.tostring(self.svg, indent=indent),
            "images": [
                image_utils.encode_image(image, image_format) for image in self.images
            ],
        }

    @classmethod
    def load(cls, svg: str, images: list[bytes]) -> "SVGDocument":
        """Load an SVGDocument from SVG content and image bytes.

        Args:
            svg: SVG content as a string.
            images: List of image bytes corresponding to <image> nodes in the SVG.
        """
        svg_node = ET.fromstring(svg)
        pil_images = [image_utils.decode_image(img_bytes) for img_bytes in images]
        return SVGDocument(svg=svg_node, images=pil_images)

    def _handle_images(
        self, embed_images: bool, image_prefix: str | None, image_format: str
    ) -> ET.Element:
        """Handle image embedding or saving."""
        svg = deepcopy(self.svg)  # Avoid modifying the original SVG.
        nodes = svg.findall(".//image")
        if len(nodes) != len(self.images):
            raise RuntimeError("Number of <image> nodes and images do not match.")

        # Handle image resources.
        if embed_images:
            for node, image in zip(nodes, self.images):
                data_uri = image_utils.encode_data_uri(image, image_format)
                node.set("href", data_uri)
        elif image_prefix:
            dirname = os.path.dirname(image_prefix)
            if dirname and not os.path.exists(dirname):
                logger.debug("Creating directory: %s", dirname)
                os.makedirs(dirname)
            for i, (node, image) in enumerate(zip(nodes, self.images), start=1):
                filepath = "{}{:02d}.{}".format(image_prefix, i, image_format.lower())
                image.save(filepath)
                node.set("href", filepath)
        else:
            raise ValueError("Either embed must be True or path must be provided.")

        return svg


def convert(input_path: str, output_path: str, image_prefix: str | None = None) -> None:
    """Convenience method to convert a PSD file to an SVG file.

    Args:
        input_path: Path to the input PSD file.
        output_path: Path to the output SVG file.
        images_path: Optional path prefix to save extracted images. If None, images will be embedded.
    """
    psdimage = PSDImage.open(input_path)
    document = SVGDocument.from_psd(psdimage)
    document.save(
        output_path, embed_images=image_prefix is None, image_prefix=image_prefix
    )
