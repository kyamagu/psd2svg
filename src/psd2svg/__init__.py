from logging import getLogger
from typing import IO, Any, Optional, Union

import svgwrite
from psd_tools import PSDImage
from psd_tools.api.layers import Layer

from psd2svg.converter.adjustments import AdjustmentsConverter
from psd2svg.converter.core import LayerConverter
from psd2svg.converter.effects import EffectsConverter
from psd2svg.converter.io import PSDReader, SVGWriter
from psd2svg.converter.shape import ShapeConverter
from psd2svg.converter.text import TextConverter
from psd2svg.version import __version__ as __version__

logger = getLogger(__name__)


def psd2svg(
    input: Union[str, IO, PSDImage, Layer],
    output: Optional[Union[str, IO]] = None,
    **kwargs: Any,
) -> Union[str, IO]:
    converter = PSD2SVG(**kwargs)
    return converter.convert(input, output)


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
        self._psd = None
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
            bbox = self._psd.viewbox

        self._dwg = svgwrite.Drawing(
            size=(bbox[2] - bbox[0], bbox[3] - bbox[1]),
            viewBox="%d %d %d %d"
            % (bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]),
        )
        if layer.is_group():
            self.create_group(layer, self._dwg)
        else:
            self._dwg.add(self.convert_layer(layer))

        # Layerless PSDImage.
        if isinstance(layer, PSDImage) and len(layer) == 0 and layer.has_preview():
            self._dwg.add(
                self._dwg.image(
                    self._get_image_href(layer.topil()),
                    insert=(0, 0),
                    size=(layer.width, layer.height),
                    debug=False,
                )
            )
        return self._save_svg()

    @property
    def width(self) -> Optional[int]:
        return self._psd.width if hasattr(self, "_psd") else None

    @property
    def height(self) -> Optional[int]:
        return self._psd.height if hasattr(self, "_psd") else None
