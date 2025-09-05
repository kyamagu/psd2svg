import logging
from typing import IO, Optional, Union

import svgwrite
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api import layers

from psd2svg.deprecated.adjustments import AdjustmentsConverter
from psd2svg.deprecated.base import ConverterProtocol
from psd2svg.deprecated.core import LayerConverter
from psd2svg.deprecated.effects import EffectsConverter
from psd2svg.deprecated.io import PSDReader, SVGWriter
from psd2svg.deprecated.shape import ShapeConverter
from psd2svg.core.svg_utils import create_node, tostring
from psd2svg.deprecated.text import TextConverter

logger = logging.getLogger(__name__)


class Converter(ConverterProtocol):
    """Converter main class."""

    def __init__(self, psdimage: PSDImage) -> None:
        # Initialize the internal state.
        self.psd = psdimage
        self.svg = create_node(
            "svg",
            width=psdimage.width,
            height=psdimage.height,
            viewBox=f"0 0 {psdimage.width} {psdimage.height}"
        )
        self.images: list[Image.Image] = []

        # Initialize the current node pointer.
        self.current = self.svg

    def __call__(self) -> str:
        """Convert the PSD image to SVG."""
        for layer in self.psd:
            self.add_layer(layer)
        return tostring(self.svg)

    def add_layer(self, layer: layers.Layer) -> None:
        """Add a layer to the svg document."""
        registry = {
            layers.Group: self.add_group,
            layers.Layer: self.add_image,
            # TODO: Add more layer types here.
        }
        handler = registry.get(type(layer), self.add_image)
        handler(layer)

    def add_group(self, group: layers.Group) -> None:
        """Add a group layer to the svg document."""
        group_node = create_node("g", parent=self.current, id=group.name)
        previous = self.current
        self.current = group_node
        for child in group:
            self.add_layer(child)
        self.current = previous

    def add_image(self, layer: layers.Layer) -> None:
        """Add an image layer to the svg document."""
        if not layer.is_visible():
            logger.debug(f"Layer '{layer.name}' is not visible.")
            return
        if not layer.has_preview():
            logger.warning(f"Layer '{layer.name}' has no preview.")
            return
        # Add a preview image.
        self.images.append(layer.composite())
        create_node(
            "image",
            parent=self.current,
            x=layer.left,
            y=layer.top,
            width=layer.width,
            height=layer.height,
        )


class PSD2SVG(
    AdjustmentsConverter,
    EffectsConverter,
    LayerConverter,
    PSDReader,
    ShapeConverter,
    SVGWriter,
    TextConverter,
):
    """PSD to SVG converter

    input_url - url, file-like object, PSDImage, or any of its layer.
    output_url - url or file-like object to export svg. if None, return data.
    export_resource - use dataURI to embed bitmap (default True)
    """

    def __init__(self, resource_path: Optional[str] = None) -> None:
        self.resource_path = resource_path

    def reset(self) -> None:
        """Reset the converter."""
        self.psd = None
        self._white_filter = None
        self._identity_filter = None
        svgwrite.utils.AutoID._set_value(0)

    def convert(
        self, layer: Union[PSDImage, Layer], output: Optional[Union[str, IO]] = None
    ) -> Union[str, IO]:
        """Convert the given PSD to SVG."""
        self.reset()
        self._set_input(layer)
        self._set_output(output)

        layer = self._layer
        bbox = layer.viewbox if hasattr(layer, "viewbox") else layer.bbox
        if bbox == (0, 0, 0, 0):
            bbox = self.psd.viewbox

        self.dwg = svgwrite.Drawing(
            size=(bbox[2] - bbox[0], bbox[3] - bbox[1]),
            viewBox="%d %d %d %d"
            % (bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]),
        )
        if layer.is_group():
            self.create_group(layer, self.dwg)
        else:
            self.dwg.add(self.convert_layer(layer))

        # Layerless PSDImage.
        if isinstance(layer, PSDImage) and len(layer) == 0 and layer.has_preview():
            self.dwg.add(
                self.dwg.image(
                    self._get_image_href(layer.topil()),
                    insert=(0, 0),
                    size=(layer.width, layer.height),
                    debug=False,
                )
            )
        return self._save_svg()

    @property
    def width(self) -> Optional[int]:
        return self.psd.width if hasattr(self, "_psd") else None

    @property
    def height(self) -> Optional[int]:
        return self.psd.height if hasattr(self, "_psd") else None
