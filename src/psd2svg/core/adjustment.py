"""Mixin for adjustment layers conversion.

Due to the limited support of BackgroundImage in SVG filters, our approach wraps
the backdrop elements into a symbol, and use two <use> elements to apply the filter.

When we have a layer structure like this::

    <layer 1 />
    <layer 2 />
    <adjustment />

We convert it into the following SVG structure::

    <symbol id="backdrop">
        <image id="layer1" ... />
        <image id="layer2" ... />
    </symbol>
    <filter id="adjustment"></filter>
    <use href="#backdrop" />
    <use href="#backdrop" filter="url(#adjustment)" />


This approach may have limitations when the backdrop has transparency, as the
stacked use elements may not produce the intended visual result.
"""

import logging
import xml.etree.ElementTree as ET

from psd_tools.api import adjustments, layers

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

    def add_invert_adjustment(
        self, layer: adjustments.Invert, **attrib: str
    ) -> ET.Element | None:
        """Add an invert adjustment layer to the svg document."""
        filter, use = self._create_filter(layer, name="invert", **attrib)
        with self.set_current(filter):
            fe_component = self.create_node(
                "feComponentTransfer", color_interpolation_filters="sRGB"
            )
            with self.set_current(fe_component):
                self.create_node("feFuncR", type="table", tableValues="1 0")
                self.create_node("feFuncG", type="table", tableValues="1 0")
                self.create_node("feFuncB", type="table", tableValues="1 0")
        return use

    def _create_filter(
        self, layer: layers.AdjustmentLayer, name: str, **attrib: str
    ) -> tuple[ET.Element, ET.Element]:
        """Create SVG filter structure for the adjustment layer."""
        wrapper = self._wrap_backdrop("symbol", id=self.auto_id("backdrop"))
        filter = self.create_node("filter", id=self.auto_id(name))
        # Backdrop use.
        self.create_node(
            "use",
            href=f"#{wrapper.get('id')}",
        )
        # Apply filter to the use.
        use = self.create_node(
            "use",
            href=f"#{wrapper.get('id')}",
            filter=f"url(#{filter.get('id')})",
            class_=name,
            **attrib,  # type: ignore[arg-type]  # Clipping context etc.
        )
        self.set_layer_attributes(layer, use)
        use = self.apply_mask(layer, use)
        return filter, use

    def _wrap_backdrop(self, tag: str = "symbol", **attrib: str) -> ET.Element:
        """Wrap previous nodes into a container node for adjustment application."""
        # TODO: Find the appropriate container in the clipping context, as the parent is mask or clipPath.
        if self.current.tag == "clipPath" or self.current.tag == "mask":
            logger.warning(
                "Wrapping backdrop inside clipping/mask context is not supported yet."
            )
        siblings = list(self.current)
        if not siblings:
            logger.warning("No backdrop elements found to wrap for adjustment.")
        wrapper = self.create_node(tag, **attrib)  # type: ignore[arg-type]
        for node in siblings:
            self.current.remove(node)
            wrapper.append(node)
        return wrapper
