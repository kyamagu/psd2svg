import logging
import xml.etree.ElementTree as ET

from psd_tools.api import effects
from psd_tools.terminology import Enum

from psd2svg.core import svg_utils
from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class EffectConverter(ConverterProtocol):
    """Effect converter mixin."""

    def add_stroke_filter(self, effect: effects.Stroke) -> ET.Element:
        """Add a stroke filter to the SVG document."""
        filter = svg_utils.create_node(
            "filter", parent=self.current, id=self.auto_id("filter_")
        )
        # TODO: Support more stroke positions.
        if effect.position in (Enum.InsetFrame, Enum.CenteredFrame):
            logger.warning(
                f"Stroke position '{effect.position}' is not supported, using 'OutsetFrame' instead."
            )
        morph = svg_utils.create_node(
            "feMorphology",
            parent=filter,
            operator="dilate",
            radius=float(effect.size),
            result="MORPH",
        )
        svg_utils.set_attribute(morph, "in", "SourceAlpha")
        composite = svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="out",
        )
        svg_utils.set_attribute(composite, "in", "MORPH")
        svg_utils.set_attribute(composite, "in2", "SourceGraphic")

        return filter
