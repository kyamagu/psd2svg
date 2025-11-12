import contextlib
import logging
from xml.etree import ElementTree as ET
from typing import Iterator

from psd_tools import PSDImage
from psd_tools.api import adjustments, layers
from psd_tools.constants import BlendMode, Tag

from psd2svg import svg_utils
from psd2svg.core.base import ConverterProtocol
from psd2svg.core.constants import BLEND_MODE, INACCURATE_BLEND_MODES

logger = logging.getLogger(__name__)


class LayerConverter(ConverterProtocol):
    """Main layer converter mixin."""

    def add_layer(self, layer: layers.Layer, **attrib: str) -> ET.Element | None:
        """Add a layer to the svg document.

        Args:
            layer: The PSD layer to add.
            attrib: Additional attributes to set on the created node.
        """
        if not layer.is_visible():
            # TODO: Option to include hidden layers.
            logger.debug(f"Layer '{layer.name}' ({layer.kind}) is invisible, skipping.")
            return None
        logger.debug(f"Adding layer: '{layer.name}' ({layer.kind})")

        # Simple registry-based dispatch.
        registry = {
            layers.Artboard: self.add_artboard,
            layers.Group: self.add_group,
            layers.PixelLayer: self.add_pixel,
            layers.ShapeLayer: self.add_shape,
            layers.SmartObjectLayer: self.add_pixel,
            layers.TypeLayer: self.add_type,
            adjustments.BlackAndWhite: self.add_adjustment,
            adjustments.BrightnessContrast: self.add_adjustment,
            adjustments.ChannelMixer: self.add_adjustment,
            adjustments.ColorBalance: self.add_adjustment,
            adjustments.ColorLookup: self.add_adjustment,
            adjustments.Curves: self.add_adjustment,
            adjustments.Exposure: self.add_adjustment,
            adjustments.GradientFill: self.add_fill,
            adjustments.GradientMap: self.add_adjustment,
            adjustments.HueSaturation: self.add_adjustment,
            adjustments.Invert: self.add_adjustment,
            adjustments.Levels: self.add_adjustment,
            adjustments.PatternFill: self.add_fill,
            adjustments.PhotoFilter: self.add_adjustment,
            adjustments.Posterize: self.add_adjustment,
            adjustments.SelectiveColor: self.add_adjustment,
            adjustments.SolidColorFill: self.add_fill,
            adjustments.Threshold: self.add_adjustment,
            adjustments.Vibrance: self.add_adjustment,
        }
        # Default layer_fn is a plain pixel layer.
        layer_fn = registry.get(type(layer), self.add_pixel)
        return layer_fn(layer, **attrib)

    def add_artboard(self, layer: layers.Artboard, **attrib: str) -> ET.Element | None:
        """Add an artboard layer to the svg document."""
        node = svg_utils.create_node(
            "svg",
            parent=self.current,
            class_=layer.kind,
            title=layer.name,
            x=layer.left,
            y=layer.top,
            width=layer.width,
            height=layer.height,
            viewBox=svg_utils.seq2str(
                [layer.left, layer.top, layer.width, layer.height]
            ),
            id=self.auto_id("artboard") if layer.has_effects() else None,
            **attrib,
        )
        with self.set_current(node):
            self.add_children(layer)
        return node

    def add_group(self, layer: layers.Group, **attrib: str) -> ET.Element | None:
        """Add a group layer to the svg document."""
        node = svg_utils.create_node(
            "g",
            parent=self.current,
            class_=layer.kind,
            title=layer.name,
            id=self.auto_id("group") if layer.has_effects() else None,
            **attrib,
        )
        with self.set_current(node):
            self.add_children(layer)

        self.apply_background_effects(layer, node, insert_before_target=True)
        self.apply_overlay_effects(layer, node)
        self.apply_stroke_effect(layer, node)
        self.set_layer_attributes(layer, node)
        return node

    def add_children(self, group: layers.Group | layers.Artboard | PSDImage) -> None:
        """Add child layers to the current node."""
        for layer in group:
            if layer.clipping or not layer.is_visible():
                continue

            if layer.has_clip_layers(visible=True):
                with self.add_clipping_target(layer) as attrib:
                    for clip_layer in layer.clip_layers:
                        self.add_layer(clip_layer, **attrib)
            else:
                # Regular layer.
                self.add_layer(layer)

    def add_pixel(self, layer: layers.Layer, **attrib: str) -> ET.Element | None:
        """Add a general pixel-based layer to the svg document."""
        if not layer.has_pixels():
            logger.warning(
                f"Layer has no pixels, skipping: '{layer.name}' ({layer.kind})."
            )
            return None

        # We will later fill in the href attribute when embedding images.
        self.images.append(layer.topil().convert("RGBA"))

        # Raster layers can have both fill opacity and overall opacity.
        fill_opacity = layer.tagged_blocks.get_data(Tag.BLEND_FILL_OPACITY, 255)

        # When the layer has effects, we need to create a separate <image> to handle fill opacity.
        if layer.has_effects():
            defs = svg_utils.create_node("defs", parent=self.current)
            node = svg_utils.create_node(
                "image",
                parent=defs,
                x=layer.left,
                y=layer.top,
                width=layer.width,
                height=layer.height,
                title=layer.name,
                id=self.auto_id("image"),
                class_=layer.kind,
                **attrib,
            )
            self.set_opacity(layer.opacity / 255, node)
            self.set_mask(layer, node)

            self.apply_background_effects(layer, node, insert_before_target=False)
            self.apply_raster_fill(layer, node)
            self.apply_overlay_effects(layer, node)
            self.apply_stroke_effect(layer, node)
        else:
            node = svg_utils.create_node(
                "image",
                parent=self.current,
                x=layer.left,
                y=layer.top,
                width=layer.width,
                height=layer.height,
                title=layer.name,
                class_=layer.kind,
                **attrib,
            )
            if fill_opacity < 255:
                self.set_opacity(fill_opacity / 255, node)
            self.set_layer_attributes(layer, node)
        return node

    def add_shape(self, layer: layers.ShapeLayer, **attrib: str) -> ET.Element | None:
        """Add a shape layer to the svg document."""
        if layer.has_effects():
            # We need to split the shape definition and effects.
            defs = svg_utils.create_node("defs", parent=self.current)
            with self.set_current(defs):
                node = self.create_shape(
                    layer,
                    title=layer.name,
                    id=self.auto_id("shape"),
                    class_=layer.kind,
                    **attrib,
                )
                self.set_opacity(layer.opacity / 255.0, node)
                self.set_mask(layer, node)

            # We need to set stroke for the shape here when fill is transparent.
            # Otherwise, effects won't use the correct alpha.
            if (
                layer.has_stroke()
                and layer.stroke.enabled
                and not layer.stroke.fill_enabled
            ):
                svg_utils.set_attribute(node, "fill", "transparent")
                self.set_stroke(layer, node)

            self.apply_background_effects(layer, node, insert_before_target=False)
            self.apply_vector_fill(layer, node)  # main filled shape.
            self.apply_overlay_effects(layer, node)
            self.apply_vector_stroke(layer, node)  # main stroke.
            self.apply_stroke_effect(layer, node)
        else:
            # We can directly create the shape.
            node = self.create_shape(
                layer, title=layer.name, class_=layer.kind, **attrib
            )
            self.set_fill(layer, node)
            self.set_stroke(layer, node)
            self.set_layer_attributes(layer, node)
        return node

    @contextlib.contextmanager
    def add_clipping_target(self, layer: layers.Layer | layers.Group) -> Iterator[dict]:
        """Context manager to handle clipping target."""
        if isinstance(layer, layers.ShapeLayer):
            with self.add_clip_path(layer) as clip_attrib:
                yield clip_attrib
        else:
            with self.add_clip_mask(layer) as clip_attrib:
                yield clip_attrib

    @contextlib.contextmanager
    def add_clip_path(self, layer: layers.ShapeLayer) -> Iterator[dict]:
        """Add a clipping path and associated elements.

        Usage::

            with self.add_clip_mask(layer) as clip_attrib:
                # Create elements inside the clipping mask.
                for clip_layer in layer.clip_layers:
                    self.add_layer(clip_layer, ..., **clip_attrib)

        Args:
            layer: The shape layer to use as a clipping path.

        Yields:
            Dictionary with clip-path attribute to apply to clipped elements.
        """
        if not layer.has_vector_mask():
            raise ValueError(f"Layer has no vector mask: '{layer.name}'")

        # Create a clipping path definition.
        clip_path = svg_utils.create_node(
            "clipPath", parent=self.current, id=self.auto_id("clip")
        )
        with self.set_current(clip_path):
            target = self.create_shape(
                layer,
                title=layer.name,
                id=self.auto_id("shape"),
                class_=layer.kind,
            )
            self.set_opacity(layer.opacity / 255.0, target)
            self.set_mask(layer, target)

        self.apply_background_effects(layer, target, insert_before_target=False)
        self.apply_vector_fill(layer, target)  # main filled shape.
        self.apply_overlay_effects(layer, target)
        # Yield to the context block.
        yield {"clip-path": svg_utils.get_funciri(clip_path)}
        self.apply_vector_stroke(layer, target)
        self.apply_stroke_effect(layer, target)

    @contextlib.contextmanager
    def add_clip_mask(self, layer: layers.Layer | layers.Group) -> Iterator[dict]:
        """Add a clipping mask and associated elements.

        Usage::

            with self.add_clip_mask(layer) as clip_attrib:
                # Create elements inside the clipping mask.
                for clip_layer in layer.clip_layers:
                    self.add_layer(clip_layer, ..., **clip_attrib)

        Args:
            layer: The layer to use as a clipping mask.

        Yields:
            Dictionary with mask attribute to apply to clipped elements.
        """

        # Create a clipping mask definition.
        mask = svg_utils.create_node(
            "mask", parent=self.current, id=self.auto_id("mask"), mask_type="alpha"
        )
        with self.set_current(mask):
            target = self.add_layer(layer)

        if target is None:
            raise ValueError(
                f"Failed to create clipping target for layer: '{layer.name}'"
            )
        if "id" not in target.attrib:
            target.set("id", self.auto_id("cliptarget"))

        self.apply_background_effects(layer, target, insert_before_target=False)
        # Create a <use> element to reference the target object.
        use = svg_utils.create_node(
            "use", parent=self.current, href=svg_utils.get_uri(target)
        )
        self.apply_overlay_effects(layer, target)
        # Yield to the context block.
        yield {"mask": svg_utils.get_funciri(mask)}
        self.apply_stroke_effect(layer, target)
        self.set_layer_attributes(layer, use)

    def add_fill(
        self,
        layer: adjustments.SolidColorFill
        | adjustments.GradientFill
        | adjustments.PatternFill,
        **attrib: str,
    ) -> ET.Element | None:
        """Add fill node to the given element."""
        logger.debug(f"Adding fill layer: '{layer.name}'")
        viewbox = layer.bbox
        if viewbox == (0, 0, 0, 0):
            viewbox = (0, 0, self.psd.width, self.psd.height)
        if layer.has_effects():
            defs = svg_utils.create_node("defs", parent=self.current)
            node = svg_utils.create_node(
                "rect",
                parent=defs,
                x=viewbox[0],
                y=viewbox[1],
                width=viewbox[2] - viewbox[0],
                height=viewbox[3] - viewbox[1],
                id=self.auto_id("fill"),
                title=layer.name,
                class_=layer.kind,
                **attrib,
            )

            self.set_opacity(layer.opacity / 255.0, node)
            self.set_mask(layer, node)
            self.apply_background_effects(layer, node, insert_before_target=False)
            self.apply_vector_fill(layer, node)  # main filled shape.
            self.apply_overlay_effects(layer, node)
            self.apply_vector_stroke(layer, node)
            self.apply_stroke_effect(layer, node)
        else:
            node = svg_utils.create_node(
                "rect",
                parent=self.current,
                x=viewbox[0],
                y=viewbox[1],
                width=viewbox[2] - viewbox[0],
                height=viewbox[3] - viewbox[1],
                title=layer.name,
                class_=layer.kind,
                **attrib,
            )
            self.set_fill(layer, node)
            self.set_layer_attributes(layer, node)
        return node

    def apply_raster_fill(self, layer: layers.Layer, node: ET.Element) -> ET.Element:
        """Add a raster main fill to the svg document."""
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(node),
        )
        fill_opacity = layer.tagged_blocks.get_data(Tag.BLEND_FILL_OPACITY, 255)
        if fill_opacity < 255:
            self.set_opacity(fill_opacity / 255, use)
        self.set_blend_mode(layer.blend_mode, use)
        return use

    def set_layer_attributes(self, layer: layers.Layer, node: ET.Element) -> None:
        """Set common layer attributes to a layer node."""
        self.set_opacity(layer.opacity / 255, node)
        self.set_blend_mode(layer.blend_mode, node)
        self.set_isolation(layer, node)
        self.set_mask(layer, node)

    def set_opacity(self, opacity: float, node: ET.Element) -> None:
        """Set opacity style to the node."""
        if opacity < 1.0:
            if "opacity" in node.attrib:
                # Combine opacities if already set.
                existing_opacity = float(node.attrib["opacity"])
                opacity *= existing_opacity
            svg_utils.set_attribute(node, "opacity", svg_utils.num2str(opacity))

    def set_blend_mode(self, psd_mode: bytes | str, node: ET.Element) -> None:
        """Set blend mode style to the node.

        Args:
            psd_mode: The Photoshop blend mode to convert.
            node: The XML element to apply the blend mode to.

        Raises:
            ValueError: If the blend mode is not supported.
        """
        if psd_mode not in BLEND_MODE:
            raise ValueError(f"Unsupported blend mode: {psd_mode!r}")

        # Warn if the blend mode is not accurately supported in SVG
        if psd_mode in INACCURATE_BLEND_MODES:
            blend_mode = BLEND_MODE[psd_mode]
            # Format the mode name for display
            mode_name = (
                psd_mode.name
                if hasattr(psd_mode, "name")
                else psd_mode.decode()
                if isinstance(psd_mode, bytes)
                else str(psd_mode)
            )
            logger.warning(
                f"Blend mode '{mode_name}' is not accurately supported in SVG. "
                f"Using approximation '{blend_mode}' instead."
            )

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
        logger.debug(f"Adding mask: '{layer.name}' ({layer.kind})")

        # Viewbox for the mask. If the mask is empty, use the full canvas.
        viewbox = layer.bbox
        if viewbox == (0, 0, 0, 0):
            viewbox = (0, 0, self.psd.width, self.psd.height)

        # Create the mask node.
        node = svg_utils.create_node(
            "mask",
            parent=self.current,
            id=self.auto_id("mask"),
        )

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
        if "transform" in target.attrib:
            # If the target has a transform, we cannot directly apply it to the mask.
            if "id" not in target.attrib:
                target.set("id", self.auto_id("masktarget"))
            defs = svg_utils.create_node("defs", parent=self.current)
            svg_utils.wrap_element(target, self.current, defs)
            svg_utils.create_node(
                "use",
                parent=self.current,
                href=svg_utils.get_uri(target),
                mask=svg_utils.get_funciri(node),
            )
        else:
            svg_utils.set_attribute(target, "mask", svg_utils.get_funciri(node))
