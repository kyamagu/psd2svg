import logging
import os

from PIL import Image
from psd_tools import PSDImage

from psd2svg.core import svg_utils
from psd2svg.core.adjustment import AdjustmentConverter
from psd2svg.core.layer import LayerConverter
from psd2svg.core.shape import ShapeConverter
from psd2svg.core.type import TypeConverter

logger = logging.getLogger(__name__)


class Converter(AdjustmentConverter, LayerConverter, ShapeConverter, TypeConverter):
    """Converter main class.

    Example usage:

        from psd2svg.core.converter import Converter

        Converter.convert("example.psd", "output.svg")
    
    Example usage:

        from psd_tools import PSDImage
        from psd2svg.core.conveter import Converter

        psd = PSDImage.open("example.psd")
        converter = Converter(psd)
        converter.build()
        converter.embed_images()  # or converter.export_images("output/image_%02d")
        svg_string = converter.export()
    
    """

    def __init__(self, psdimage: PSDImage) -> None:
        """Initialize the converter internal state."""

        # Source PSD image.
        if not isinstance(psdimage, PSDImage):
            raise TypeError("psdimage must be an instance of PSDImage")
        self.psd = psdimage

        # Initialize the SVG root element.
        self.svg = svg_utils.create_node(
            "svg",
            width=psdimage.width,
            height=psdimage.height,
            viewBox=f"0 0 {psdimage.width} {psdimage.height}",
        )
        self.images: list[Image.Image] = []  # Store PIL images here.

        # Initialize the current node pointer.
        self.current = self.svg

    def build(self) -> None:
        """Build the SVG structure and internally store the result."""
        assert self.psd is not None, "PSD image is not set."
        for layer in self.psd:
            self.add_layer(layer)

    def embed_images(self) -> None:
        """Embed images as base64 data URIs."""
        nodes = self.svg.findall(".//image")
        if len(nodes) != len(self.images):
            raise RuntimeError("Number of <image> nodes and images do not match.")
        for node, image in zip(nodes, self.images):
            data_uri = svg_utils.encode_data_uri(image)
            node.set("href", data_uri)

    def export_images(self, output_prefix: str = "images/") -> None:
        """Export images to the specified directory."""
        dirname = os.path.dirname(output_prefix)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)

        nodes = self.svg.findall(".//image")
        if len(nodes) != len(self.images):
            raise RuntimeError("Number of <image> nodes and images do not match.")
        for i, (node, image) in enumerate(zip(nodes, self.images), start=1):
            filepath = "{}{:02d}.png".format(output_prefix, i)
            image.save(filepath)
            node.set("href", filepath)

    def export(self, indent: str = "  ") -> str:
        """Export the SVG as a string."""
        return svg_utils.tostring(self.svg, indent=indent)

    def save(self, filepath: str) -> None:
        """Save the SVG to a file."""
        with open(filepath, "w", encoding="utf-8") as f:
            svg_utils.write(self.svg, f)

    @classmethod
    def convert(cls, input_path: str, output_path: str, images_path: str | None = None) -> None:
        """Convenience method to convert a PSD file to SVG."""
        psdimage = PSDImage.open(input_path)
        converter = Converter(psdimage)
        converter.build()
        if images_path:
            converter.export_images(images_path)
        else:
            converter.embed_images()
        converter.save(output_path)