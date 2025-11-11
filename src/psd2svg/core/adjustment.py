import logging
import xml.etree.ElementTree as ET

from psd_tools.api import layers

from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class AdjustmentConverter(ConverterProtocol):
    """Mixin for adjustment layers."""

    def add_adjustment(
        self, layer: layers.AdjustmentLayer, **attrib: str
    ) -> ET.Element | None:
        """Add an adjustment layer to the svg document."""
        logger.warning(
            f"Adjustment layer is unsupported yet: '{layer.name}' ({layer.kind})"
        )
        return None
