import logging
from xml.etree import ElementTree as ET

from psd_tools import PSDImage
from psd_tools.api import adjustments, layers
from psd_tools.constants import BlendMode

from psd2svg import svg_utils
from psd2svg.core.base import ConverterProtocol
from psd2svg.core.constants import BLEND_MODE
from psd2svg.core.counter import AutoCounter

logger = logging.getLogger(__name__)


class LayerConverter(ConverterProtocol):
    """Main layer converter mixin."""

    _id_counter: AutoCounter | None = None

    def auto_id(self, prefix: str = "") -> str:
        """Generate a unique ID for SVG elements."""
        if self._id_counter is None:
            self._id_counter = AutoCounter()
        return self._id_counter.get_id(prefix)

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
        }
        # Default layer_fn is a plain pixel layer.
        layer_fn = registry.get(type(layer), self.add_pixel)
        return layer_fn(layer)

    def add_group(self, layer: layers.Artboard | layers.Group) -> ET.Element:
        """Add a group layer to the svg document."""
        node = svg_utils.create_node(
            "g",
            parent=self.current,
            class_=layer.kind,
            title=layer.name,
            id=self.auto_id("group") if layer.has_effects() else None,
        )
        with self.set_current(node):
            self.add_children(layer)
        
        self.apply_drop_shadow_effect(layer, node, insert_before_target=True)
        self.apply_outer_glow_effect(layer, node, insert_before_target=True)
        self.apply_color_overlay_effect(layer, node)
        self.apply_inner_shadow_effect(layer, node)
        self.apply_inner_glow_effect(layer, node)
        self.apply_satin_effect(layer, node)
        self.apply_bevel_emboss_effect(layer, node)
        self.apply_stroke_effect(layer, node)
        self.set_layer_attributes(layer, node)
        return node

    def add_children(self, group: layers.Group | layers.Artboard | PSDImage) -> None:
        """Add child layers to the current node."""
        for layer in group:
            if layer.clipping or not layer.is_visible():
                continue

            if layer.has_clip_layers(visible=True):
                with self.add_clipping_target(layer):
                    for clip_layer in layer.clip_layers:
                        self.add_layer(clip_layer)
            else:
                # Regular layer.
                self.add_layer(layer)

    def add_pixel(self, layer: layers.Layer) -> ET.Element | None:
        """Add a general pixel-based layer to the svg document."""
        if not layer.has_pixels():
            logger.debug(f"Layer '{layer.name}' has no pixels.")
            return None
        self.images.append(layer.topil().convert("RGBA"))
        node = svg_utils.create_node(
            "image",
            parent=self.current,
            x=layer.left,
            y=layer.top,
            width=layer.width,
            height=layer.height,
            title=layer.name,
            id=self.auto_id("image") if layer.has_effects() else None,
        )
        self.apply_drop_shadow_effect(layer, node, insert_before_target=True)
        self.apply_outer_glow_effect(layer, node, insert_before_target=True)
        self.apply_color_overlay_effect(layer, node)
        self.apply_inner_shadow_effect(layer, node)
        self.apply_inner_glow_effect(layer, node)
        self.apply_satin_effect(layer, node)
        self.apply_bevel_emboss_effect(layer, node)
        self.apply_stroke_effect(layer, node)
        self.set_layer_attributes(layer, node)
        return node

    def set_layer_attributes(self, layer: layers.Layer, node: ET.Element) -> None:
        """Set common layer attributes to a layer node."""
        self.set_opacity(layer.opacity / 255, node)
        self.set_blend_mode(layer.blend_mode, node)
        self.set_isolation(layer, node)
        self.set_mask(layer, node)

        svg_utils.add_class(node, layer.kind)  # Keep the layer type as class.

    def set_opacity(self, opacity: float, node: ET.Element) -> None:
        """Set opacity style to the node."""
        if opacity < 1.0:
            svg_utils.set_attribute(node, "opacity", opacity)

    def set_blend_mode(self, psd_mode: bytes | str, node: ET.Element) -> None:
        """Set blend mode style to the node."""
        if psd_mode not in BLEND_MODE:
            logger.warning(f"Unsupported blend mode: {psd_mode!r}")
            return
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
        if (
            isinstance(layer, layers.Group)
            and layer.blend_mode != BlendMode.PASS_THROUGH
        ):
            svg_utils.add_style(node, "isolation", "isolate")

    def set_mask(self, layer: layers.Layer, target: ET.Element) -> None:
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
            "mask", parent=self.current, id=self.auto_id("mask")
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
                fill="#ffffff",
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
