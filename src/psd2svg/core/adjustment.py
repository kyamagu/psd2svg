import logging
import xml.etree.ElementTree as ET

from psd_tools.api import layers

from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class AdjustmentConverter(ConverterProtocol):
    """Mixin for adjustment layers."""

    def add_adjustment(self, layer: layers.AdjustmentLayer) -> ET.Element | None:
        """Add an adjustment layer to the svg document."""
        logger.info("Adding adjustment layer: %s", layer.name)
        return None
        # # Handle different types of adjustment layers.
        # adjustment_type = type(layer.adjustment)
        # if adjustment_type == layers.BrightnessContrast:
        #     self._add_brightness_contrast(layer)
        # elif adjustment_type == layers.Levels:
        #     self._add_levels(layer)
        # elif adjustment_type == layers.Curves:
        #     self._add_curves(layer)
        # elif adjustment_type == layers.HueSaturation:
        #     self._add_hue_saturation(layer)
        # elif adjustment_type == layers.ColorBalance:
        #     self._add_color_balance(layer)
        # elif adjustment_type == layers.BlackWhite:
        #     self._add_black_white(layer)
        # elif adjustment_type == layers.PhotoFilter:
        #     self._add_photo_filter(layer)
        # elif adjustment_type == layers.Invert:
        #     self._add_invert(layer)
        # elif adjustment_type == layers.Posterize:
        #     self._add_posterize(layer)
        # elif adjustment_type == layers.Threshold:
        #     self._add_threshold(layer)
        # elif adjustment_type == layers.SelectiveColor:
        #     self._add_selective_color(layer)
        # else:
        #     logger.warning(f"Unsupported adjustment layer type: {adjustment_type}")