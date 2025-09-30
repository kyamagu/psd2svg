import logging
from xml.etree import ElementTree as ET

from psd_tools import PSDImage
from psd_tools.api import adjustments, layers
from psd_tools.constants import BlendMode

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
            layers.Artboard: self.add_group,
            layers.Group: self.add_group,
            adjustments.SolidColorFill: self.add_fill,
            layers.ShapeLayer: self.add_shape,
            # layers.TypeLayer: self.add_type,
            layers.PixelLayer: self.add_pixel,
        }
        # Default layer_fn is a plain pixel layer.
        layer_fn = registry.get(type(layer), self.add_pixel)
        node = layer_fn(layer)
        if node is not None:
            # TODO: Node-less layers, e.g. adjustment.
            self.set_layer_attributes(layer, node)
        return node

    def add_group(self, group: layers.Artboard | layers.Group) -> ET.Element | None:
        """Add a group layer to the svg document."""
        group_node = svg_utils.create_node(
            "g", parent=self.current, class_=group.kind, title=group.name
        )
        with self.set_current(group_node):
            self._add_children(group)
        return group_node

    def _add_children(self, group: layers.Group | layers.Artboard | PSDImage) -> None:
        """Add child layers to the current node."""
        for layer in group:
            if (
                layer.has_clip_layers()
                and layer.is_visible()
                and any(clip_layer.is_visible() for clip_layer in layer.clip_layers)
            ):
                with self.add_clipping_target(layer):
                    for clip_layer in layer.clip_layers:
                        self.add_layer(clip_layer)
            elif layer.clipping_layer:
                continue
            else:
                # Regular layer.
                self.add_layer(layer)

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
            title=layer.name,
        )

    def set_layer_attributes(self, layer: layers.Layer, node: ET.Element) -> None:
        """Set common layer attributes to a layer node."""
        if layer.opacity < 255:
            svg_utils.set_attribute(node, "opacity", layer.opacity / 255)

        self.set_blend_mode(layer.blend_mode, node)
        self.set_isolation(layer, node)
        self.set_mask(layer, node)

        svg_utils.add_class(node, layer.kind)  # Keep the layer type as class.

    def set_blend_mode(self, psd_mode: bytes | str, node: ET.Element) -> None:
        """Set blend mode style to the node."""
        blend_mode = BLEND_MODE[psd_mode]
        if blend_mode not in ("normal", "pass-through"):
            svg_utils.add_style(node, "mix-blend-mode", blend_mode)

    def set_isolation(self, layer: layers.Layer, node: ET.Element) -> None:
        """Add isolation to a group.

        NOTE:
          1. The default blending mode of a PSD group is passthrough, which corresponds to SVG isolation: auto (default)
          2. When the group has blending mode normal, it corresponds to SVG isolation: isolate.
          3. Other blending modes also isolate the group,
             and in SVG setting mix-blend-mode on a <g> to a value other than normal isolates the group by default.
        """
        if isinstance(layer, layers.Group) and layer.blend_mode != BlendMode.PASS_THROUGH:
            svg_utils.add_style(node, "isolation", "isolate")

    def set_mask(self, layer: layers.Layer, target: ET.Element) -> ET.Element | None:
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
        # svg_utils.set_attribute(node, "color-interpolation", "sRGB")

        # If the mask has a background color (invert mask), add a white rectangle first.
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
        svg_utils.set_attribute(target, "mask", svg_utils.get_funciri(node))
        return node
