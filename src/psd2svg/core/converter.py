import logging

from PIL import Image
from psd_tools import PSDImage

from psd2svg import svg_utils
from psd2svg.core.adjustment import AdjustmentConverter
from psd2svg.core.effects import EffectConverter
from psd2svg.core.layer import LayerConverter
from psd2svg.core.shape import ShapeConverter
from psd2svg.core.type import TypeConverter

logger = logging.getLogger(__name__)


class Converter(
    AdjustmentConverter, LayerConverter, ShapeConverter, TypeConverter, EffectConverter
):
    """Converter main class.

    Example usage:

        from psd2svg.core.converter import Converter

        Converter.convert("example.psd", "output.svg")

    Example usage:

        from psd_tools import PSDImage
        from psd2svg.core.conveter import Converter

        psd = PSDImage.open("example.psd")
        converter = Converter(psd)
        document = converter.build()
        document.embed_images()  # or document.export_images("output/image_%02d")
        svg_string = document.export()

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
            xmlns=svg_utils.NAMESPACE,
            width=psdimage.width,
            height=psdimage.height,
            viewBox=svg_utils.seq2str([0, 0, psdimage.width, psdimage.height], sep=" "),
        )
        self.images: list[Image.Image] = []  # Store PIL images here.

        # Initialize the current node pointer.
        self.current = self.svg

    def build(self) -> None:
        """Build the SVG structure and internally save the result."""
        assert self.psd is not None, "PSD image is not set."

        if len(self.psd) == 0 and self.psd.has_preview():
            # Special case: No layers, just a flat image.
            svg_utils.create_node(
                "image",
                parent=self.current,
                width=self.psd.width,
                height=self.psd.height,
            )
            self.images.append(self.psd.composite())
        else:
            self.add_children(self.psd)
