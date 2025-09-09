import logging
from xml.etree import ElementTree as ET

from psd_tools.api import layers

from psd2svg.core import svg_utils
from psd2svg.core.base import ConverterProtocol
from psd2svg.core.constants import BLEND_MODE

logger = logging.getLogger(__name__)


class LayerConverter(ConverterProtocol):
    """Main layer converter mixin."""

    _id_counter = 0

    def auto_id(self, prefix: str = "") -> str:
        """Generate a unique ID for SVG elements."""
        self._id_counter += 1
        return f"{prefix}{self._id_counter:g}"

    def add_layer(self, layer: layers.Layer) -> ET.Element | None:
        """Add a layer to the svg document."""
        if not layer.is_visible():
            # TODO: Option to include hidden layers.
            logger.debug(f"Layer '{layer.name}' is invisible.")
            return None
        logger.debug(f"Adding layer: '{layer.name}' ({layer.kind})")

        # Simple registry-based dispatch.
        registry = {
            # TODO: Support more layer types here.
            layers.Group: self.add_group,
            # layers.AdjustmentLayer: self.add_adjustment,
            # layers.ShapeLayer: self.add_shape,
            # layers.TypeLayer: self.add_type,
            layers.PixelLayer: self.add_pixel,
        }
        # Default handler is a plain pixel layer.
        handler = registry.get(type(layer), self.add_pixel)
        node = handler(layer)
        if node is not None:
            self.add_attributes(layer, node)
            self.add_mask(layer, node)
        return node

    def add_group(self, group: layers.Group) -> ET.Element | None:
        """Add a group layer to the svg document."""
        previous = self.current  # type: ignore
        group_node = svg_utils.create_node(
            "g", parent=previous, class_="group", title=group.name
        )
        self.current = group_node
        for child in group:
            self.add_layer(child)
        self.current = previous
        return group_node

    def add_pixel(self, layer: layers.Layer) -> ET.Element | None:
        """Add a general pixel-based layer to the svg document."""
        if not layer.has_pixels():
            logger.debug(f"Layer '{layer.name}' has no pixels.")
            return None

        self.images.append(layer.topil().convert("RGBA"))
        return svg_utils.create_node(
            "image",
            parent=self.current,
            x=layer.left,
            y=layer.top,
            width=layer.width,
            height=layer.height,
            class_=layer.kind,
            title=layer.name,
        )

    def add_attributes(self, layer: layers.Layer, node: ET.Element) -> None:
        """Add common attributes to a layer node."""
        if layer.opacity < 255:
            node.set("opacity", f"{layer.opacity / 255:.2g}")
        blend_mode = BLEND_MODE[layer.blend_mode]
        if blend_mode != "normal":
            svg_utils.add_style(node, "mix-blend-mode", blend_mode)

    def add_mask(self, layer: layers.Layer, target: ET.Element) -> ET.Element | None:
        """Add a mask to a layer node."""
        if (
            not layer.has_mask()
            or layer.mask.disabled
            or layer.mask.width == 0
            or layer.mask.height == 0
        ):
            return None
        logger.debug(f"Adding mask: '{layer.name}'")

        # Viewbox for the mask. If the mask is empty, use the full canvas.
        viewbox = layer.bbox
        if viewbox == (0, 0, 0, 0):
            viewbox = (0, 0, self.psd.width, self.psd.height)

        # Create the mask node.
        node = svg_utils.create_node(
            "mask", parent=self.current, id=self.auto_id("mask_")
        )
        # TODO: Check layer mask attributes.
        # node["color-interpolation"] = "sRGB"

        # If the mask has a background color, add a white rectangle first.
        if layer.mask.background_color > 0:
            svg_utils.create_node(
                "rect",
                parent=node,
                x=viewbox[0],
                y=viewbox[1],
                width=viewbox[2] - viewbox[0],
                height=viewbox[3] - viewbox[1],
                fill="white",
            )
        
        # Mask image.
        self.images.append(layer.mask.topil().convert("L"))
        svg_utils.create_node(
            "image",
            parent=node,
            x=layer.mask.left,
            y=layer.mask.top,
            width=layer.mask.width,
            height=layer.mask.height,
        )
        target.set("mask", f"url(#{node.get('id')})")
        return node
