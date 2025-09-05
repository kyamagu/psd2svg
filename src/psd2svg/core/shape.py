import logging
import xml.etree.ElementTree as ET

from psd_tools.api import layers

from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class ShapeConverter(ConverterProtocol):
    """Mixin for shape layers."""

    def add_shape(self, layer: layers.ShapeLayer) -> ET.Element | None:
        """Add a shape layer to the svg document."""
        logger.info("Adding shape layer: %s", layer.name)
        return None