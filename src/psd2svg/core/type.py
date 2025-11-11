import logging
import xml.etree.ElementTree as ET

from psd_tools.api import layers

from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class TypeConverter(ConverterProtocol):
    """Mixin for type layers."""

    def add_type(self, layer: layers.TypeLayer, **attrib: str) -> ET.Element | None:
        """Add a type layer to the svg document."""
        logger.debug(
            f"Type layer support is raster only: '{layer.name}' ({layer.kind})"
        )
        return self.add_pixel(layer, **attrib)
