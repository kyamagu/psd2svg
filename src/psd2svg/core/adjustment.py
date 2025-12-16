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

from psd2svg import svg_utils
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

    def add_posterize_adjustment(
        self, layer: adjustments.Posterize, **attrib: str
    ) -> ET.Element | None:
        """Add a posterize adjustment layer to the svg document."""
        # Validate and clamp levels to valid range
        levels = layer.posterize
        if levels < 2:
            logger.warning(
                f"Posterize levels {levels} is below minimum (2), clamping to 2"
            )
            levels = 2
        elif levels > 256:
            logger.warning(
                f"Posterize levels {levels} exceeds maximum (256), clamping to 256"
            )
            levels = 256

        # Generate discrete table values: [0/(n-1), 1/(n-1), ..., (n-1)/(n-1)]
        table_values = [i / (levels - 1) for i in range(levels)]
        table_values_str = svg_utils.seq2str(table_values, sep=" ")

        filter, use = self._create_filter(layer, name="posterize", **attrib)
        with self.set_current(filter):
            fe_component = self.create_node(
                "feComponentTransfer", color_interpolation_filters="sRGB"
            )
            with self.set_current(fe_component):
                # Apply discrete posterization to RGB channels
                self.create_node(
                    "feFuncR", type="discrete", tableValues=table_values_str
                )
                self.create_node(
                    "feFuncG", type="discrete", tableValues=table_values_str
                )
                self.create_node(
                    "feFuncB", type="discrete", tableValues=table_values_str
                )
        return use

    def add_huesaturation_adjustment(
        self, layer: adjustments.HueSaturation, **attrib: str
    ) -> ET.Element | None:
        """Add a hue/saturation adjustment layer to the svg document.

        Supports two modes:
        - Normal mode: Adjusts hue, saturation, and lightness using master values
        - Colorize mode: Desaturates then applies colorization tint

        Note: Per-range color adjustments (layer.data) are not yet supported.
        """
        # Extract adjustment parameters
        hue, saturation, lightness = layer.master
        enable_colorization = layer.enable_colorization

        # Check if this is a no-op adjustment
        if enable_colorization == 0 and hue == 0 and saturation == 0 and lightness == 0:
            logger.info(
                f"HueSaturation adjustment '{layer.name}' has no effect, skipping"
            )
            return None

        # Create filter structure
        filter, use = self._create_filter(layer, name="huesaturation", **attrib)

        with self.set_current(filter):
            if enable_colorization == 1:
                # Colorize mode: desaturate, then apply colorization
                self._apply_colorize_mode(layer)
            else:
                # Normal mode: apply master adjustments
                self._apply_normal_huesaturation(hue, saturation, lightness)

        return use

    def _apply_normal_huesaturation(
        self, hue: int, saturation: int, lightness: int
    ) -> None:
        """Apply normal mode hue/saturation adjustments."""
        # Apply lightness decrease first (darkening)
        if lightness < 0:
            slope = 1 + (lightness / 100)
            fe_component = self.create_node(
                "feComponentTransfer", color_interpolation_filters="sRGB"
            )
            with self.set_current(fe_component):
                for func in ["feFuncR", "feFuncG", "feFuncB"]:
                    self.create_node(func, type="linear", slope=slope, intercept=0)

        # Apply hue rotation
        if hue != 0:
            self.create_node(
                "feColorMatrix",
                type="hueRotate",
                values=hue,
                color_interpolation_filters="sRGB",
            )

        # Apply saturation adjustment
        if saturation != 0:
            saturate_factor = 1 + (saturation / 100)
            self.create_node(
                "feColorMatrix",
                type="saturate",
                values=saturate_factor,
                color_interpolation_filters="sRGB",
            )

        # Apply lightness increase (brightening)
        if lightness > 0:
            slope = 1 - (lightness / 100)
            intercept = lightness / 100
            fe_component = self.create_node(
                "feComponentTransfer", color_interpolation_filters="sRGB"
            )
            with self.set_current(fe_component):
                for func in ["feFuncR", "feFuncG", "feFuncB"]:
                    self.create_node(
                        func, type="linear", slope=slope, intercept=intercept
                    )

    def _apply_colorize_mode(self, layer: adjustments.HueSaturation) -> None:
        """Apply colorize mode adjustments."""
        hue, saturation, lightness = layer.colorization

        # Step 1: Desaturate completely
        self.create_node(
            "feColorMatrix",
            type="saturate",
            values=0,
            color_interpolation_filters="sRGB",
        )

        # Step 2: Apply colorization hue rotation
        if hue != 0:
            self.create_node(
                "feColorMatrix",
                type="hueRotate",
                values=hue,
                color_interpolation_filters="sRGB",
            )

        # Step 3: Apply colorization saturation (absolute, not delta)
        # Note: Photoshop's colorization saturation is 0-100, not -100 to +100
        saturate_factor = 1 + (saturation / 100)
        self.create_node(
            "feColorMatrix",
            type="saturate",
            values=saturate_factor,
            color_interpolation_filters="sRGB",
        )

        # Step 4: Apply lightness adjustment
        if lightness != 0:
            if lightness < 0:
                slope = 1 + (lightness / 100)
                intercept = 0
            else:
                slope = 1 - (lightness / 100)
                intercept = lightness / 100

            fe_component = self.create_node(
                "feComponentTransfer", color_interpolation_filters="sRGB"
            )
            with self.set_current(fe_component):
                for func in ["feFuncR", "feFuncG", "feFuncB"]:
                    self.create_node(
                        func, type="linear", slope=slope, intercept=intercept
                    )

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
