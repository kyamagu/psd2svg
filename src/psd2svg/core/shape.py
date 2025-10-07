import contextlib
import logging
import xml.etree.ElementTree as ET
from typing import Iterator

from psd_tools.api import adjustments, layers
from psd_tools.api.shape import VectorMask, Rectangle, RoundedRectangle, Ellipse
from psd_tools.constants import Tag
from psd_tools.terminology import Klass

from psd2svg.core import color_utils, svg_utils
from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class ShapeConverter(ConverterProtocol):
    """Mixin for shape layers."""

    def add_shape(self, layer: layers.ShapeLayer) -> ET.Element | None:
        """Add a shape layer to the svg document."""
        if layer.has_effects():
            # We need to split the shape definition and effects.
            defs = svg_utils.create_node("defs", parent=self.current)
            with self.set_current(defs):
                node = self._create_shape(layer, id=self.auto_id("shape_"))

            self.apply_drop_shadow_effect(layer, node)
            self.apply_outer_glow_effect(layer, node)
            use = self.apply_vector_fill(layer, node)
            self.apply_color_overlay_effect(layer, node)
            self.apply_vector_stroke(layer, node)
            self.apply_stroke_effect(layer, node)
            # NOTE: Prevent set_layer_attributes from overriding these.
            return use
        else:
            node = self._create_shape(layer)
            self.set_fill(layer, node)
            self.set_stroke(layer, node)
            return node

    def add_fill(self, layer: adjustments.SolidColorFill) -> ET.Element | None:
        """Add fill node to the given element."""
        logger.debug(f"Adding fill layer: '{layer.name}'")
        viewbox = layer.bbox
        if viewbox == (0, 0, 0, 0):
            viewbox = (0, 0, self.psd.width, self.psd.height)
        if layer.has_effects():
            defs = svg_utils.create_node("defs", parent=self.current)
            with self.set_current(defs):
                node = svg_utils.create_node(
                    "rect",
                    x=viewbox[0],
                    y=viewbox[1],
                    width=viewbox[2] - viewbox[0],
                    height=viewbox[3] - viewbox[1],
                    id=self.auto_id("fill_"),
                    title=layer.name,
                )
            self.apply_drop_shadow_effect(layer, node)
            self.apply_outer_glow_effect(layer, node)
            use = self.apply_vector_fill(layer, node)
            self.apply_color_overlay_effect(layer, node)
            return use
        else:
            node = svg_utils.create_node(
                "rect",
                parent=self.current,
                x=viewbox[0],
                y=viewbox[1],
                width=viewbox[2] - viewbox[0],
                height=viewbox[3] - viewbox[1],
                title=layer.name,
            )
            self.set_fill(layer, node)
            return node

    def _create_shape(self, layer: layers.ShapeLayer, **attrib) -> ET.Element:
        if layer.has_origination():
            if len(layer.origination) > 1:
                logger.warning("Multiple origination shapes are not supported yet.")
            origination = layer.origination[0]
            if isinstance(origination, Rectangle):
                node = self.create_origination_rectangle(
                    origination, title=layer.name, **attrib
                )
            elif isinstance(origination, RoundedRectangle):
                node = self.create_origination_rounded_rectangle(
                    origination, title=layer.name, **attrib
                )
            elif isinstance(origination, Ellipse):
                node = self.create_origination_ellipse(
                    origination, title=layer.name, **attrib
                )
            # # Line shape is not supported, as this can be an arrow. <line> or <marker>.
            # elif isinstance(shape, Line):
            #     node = svg_utils.create_node(
            #         "line",
            #         parent=self.current,
            #         x1=shape.line_start[Enum.Horizontal],
            #         y1=shape.line_start[Enum.Vertical],
            #         x2=shape.line_end[Enum.Horizontal],
            #         y2=shape.line_end[Enum.Vertical],
            #         title=layer.name,
            #     )
            else:
                logger.debug(
                    f"Unsupported shape type: {type(origination)}: {origination._data}"
                )
                node = self.create_path(layer, **attrib)
        else:
            node = self.create_path(layer, **attrib)
        return node

    def create_origination_rectangle(
        self, origination: Rectangle, **attrib
    ) -> ET.Element:
        """Create a rectangle shape from origination data."""

        return svg_utils.create_node(
            "rect",
            parent=self.current,
            x=int(origination.bbox[0]),
            y=int(origination.bbox[1]),
            width=int(origination.bbox[2] - origination.bbox[0]),
            height=int(origination.bbox[3] - origination.bbox[1]),
            **attrib,
        )

    def create_origination_rounded_rectangle(
        self, origination: RoundedRectangle, **attrib
    ) -> ET.Element:
        """Create a rounded rectangle shape from origination data."""
        rx = (
            float(origination.radii[b"topRight"])
            + float(origination.radii[b"bottomRight"])
        ) / 2
        ry = (
            float(origination.radii[b"topRight"]) + float(origination.radii[b"topLeft"])
        ) / 2
        return svg_utils.create_node(
            "rect",
            parent=self.current,
            x=int(origination.bbox[0]),
            y=int(origination.bbox[1]),
            width=int(origination.bbox[2] - origination.bbox[0]),
            height=int(origination.bbox[3] - origination.bbox[1]),
            rx=rx,
            ry=ry,
            **attrib,
        )

    def create_origination_ellipse(self, origination: Ellipse, **attrib) -> ET.Element:
        """Create an ellipse shape from origination data."""
        cx = (origination.bbox[0] + origination.bbox[2]) / 2
        cy = (origination.bbox[1] + origination.bbox[3]) / 2
        rx = (origination.bbox[2] - origination.bbox[0]) / 2
        ry = (origination.bbox[3] - origination.bbox[1]) / 2
        return svg_utils.create_node(
            "ellipse",
            parent=self.current,
            cx=int(cx),
            cy=int(cy),
            rx=rx,
            ry=ry,
            **attrib,
        )

    @contextlib.contextmanager
    def add_clipping_target(self, layer: layers.Layer | layers.Group) -> Iterator[None]:
        """Context manager to handle clipping target."""
        if isinstance(layer, layers.ShapeLayer):
            with self.add_clip_path(layer):
                yield
        else:
            with self.add_clip_mask(layer):
                yield

    @contextlib.contextmanager
    def add_clip_path(self, layer: layers.ShapeLayer) -> Iterator[None]:
        """Add a clipping path and associated elements."""

        # TODO: Support live shapes (layer origination).
        if not layer.has_vector_mask():
            raise ValueError("Layer has no vector mask: %s", layer.name)

        # Create a clipping path definition.
        clip_path = svg_utils.create_node(
            "clipPath", parent=self.current, id=self.auto_id("clip_")
        )
        with self.set_current(clip_path):
            target = self._create_shape(layer, id=self.auto_id("shape_"))

        self.apply_drop_shadow_effect(layer, target)
        self.apply_outer_glow_effect(layer, target)
        self.apply_vector_fill(layer, target)
        self.apply_color_overlay_effect(layer, target)

        # Create a group with the clipping path applied.
        group = svg_utils.create_node(
            "g", parent=self.current, clip_path=svg_utils.get_funciri(clip_path)
        )
        with self.set_current(group):
            yield  # Yield to the context block.

        # TODO: Inner filter effects on clipping path.
        self.apply_vector_stroke(layer, target)
        self.apply_stroke_effect(layer, target)

    def apply_vector_fill(self, layer: layers.Layer, target: ET.Element) -> ET.Element:
        """Apply fill effects to the target element."""
        # TODO: Check if the layer has fill.
        use = svg_utils.create_node(
            "use", parent=self.current, href=svg_utils.get_uri(target)
        )
        self.set_fill(layer, use)
        return use

    def apply_vector_stroke(self, layer: layers.Layer, target: ET.Element) -> None:
        """Apply stroke effects to the target element."""
        if layer.has_stroke() and layer.stroke.enabled:
            use = svg_utils.create_node(
                "use",
                parent=self.current,
                href=svg_utils.get_uri(target),
                fill="transparent",
            )
            self.set_stroke(layer, use)

    @contextlib.contextmanager
    def add_clip_mask(self, layer: layers.Layer | layers.Group) -> Iterator[None]:
        """Add a clipping mask and associated elements."""

        # Create a clipping mask definition.
        mask = svg_utils.create_node(
            "mask", parent=self.current, id=self.auto_id("mask_"), mask_type="alpha"
        )
        with self.set_current(mask):
            target = self.add_layer(layer)  # TODO: Check attributes for later <use>.

        if target is None:
            raise ValueError(
                "Failed to create clipping target for layer: %s", layer.name
            )
        if "id" not in target.attrib:
            target.set("id", self.auto_id("cliptarget_"))

        self.apply_drop_shadow_effect(layer, target)
        self.apply_outer_glow_effect(layer, target)
        # Create a <use> element to reference the target object.
        svg_utils.create_node(
            "use", parent=self.current, href=svg_utils.get_uri(target)
        )
        self.apply_color_overlay_effect(layer, target)

        # Create a group with the clipping mask applied.
        group = svg_utils.create_node(
            "g", parent=self.current, mask=svg_utils.get_funciri(mask)
        )
        with self.set_current(group):
            yield  # Yield to the context block.

        self.apply_stroke_effect(layer, target)

    def create_path(self, layer: layers.Layer, **attrib) -> ET.Element:
        """Create a path element."""
        if not layer.has_vector_mask():
            raise ValueError("Layer has no vector mask: %s", layer.name)

        path = svg_utils.create_node(
            "path",
            parent=self.current,
            d=self.generate_path(layer.vector_mask),
            title=layer.name,
            **attrib,
        )
        if layer.vector_mask.initial_fill_rule:
            logger.warning("Initial fill rule (inverted mask) is not supported yet.")
        # svg_utils.set_attribute(path, "fill-rule", "evenodd")
        return path

    def generate_path(
        self: ConverterProtocol,
        vector_mask: VectorMask,
        command: str = "C",
    ) -> str:
        """Sequence generator for SVG path constructor."""

        # TODO: Implement even-odd rule for multiple paths.
        # first path --> show, second path --> hide, third path --> show.
        # should be clipPath.
        def _do_generate():
            for path in vector_mask.paths:
                if len(path) == 0:
                    continue

                # Initial point.
                yield "M"
                yield ",".join(
                    [
                        svg_utils.num2str(path[0].anchor[1] * self.psd.width),
                        svg_utils.num2str(path[0].anchor[0] * self.psd.height),
                    ]
                )

                # Closed path or open path
                points = (
                    zip(path, path[1:] + path[0:1])
                    if path.is_closed()
                    else zip(path, path[1:])
                )

                # Rest of the points.
                yield command
                for p1, p2 in points:
                    yield ",".join(
                        [
                            svg_utils.num2str(p1.leaving[1] * self.psd.width),
                            svg_utils.num2str(p1.leaving[0] * self.psd.height),
                        ]
                    )
                    yield ",".join(
                        [
                            svg_utils.num2str(p2.preceding[1] * self.psd.width),
                            svg_utils.num2str(p2.preceding[0] * self.psd.height),
                        ]
                    )
                    yield ",".join(
                        [
                            svg_utils.num2str(p2.anchor[1] * self.psd.width),
                            svg_utils.num2str(p2.anchor[0] * self.psd.height),
                        ]
                    )

                if path.is_closed():
                    yield "Z"

        return " ".join(str(x) for x in _do_generate())

    def set_fill(self, layer: layers.Layer, node: ET.Element) -> None:
        """Set fill attribute to the given element."""
        if Tag.VECTOR_STROKE_CONTENT_DATA in layer.tagged_blocks:
            content_data = layer.tagged_blocks.get_data(Tag.VECTOR_STROKE_CONTENT_DATA)
            if Klass.Color in content_data:
                color = color_utils.descriptor2hex(content_data[Klass.Color])
                svg_utils.set_attribute(node, "fill", color)
            else:
                logger.warning(f"Unsupported fill content: {content_data}")
        elif Tag.SOLID_COLOR_SHEET_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.SOLID_COLOR_SHEET_SETTING)
            color = color_utils.descriptor2hex(setting[Klass.Color])
            svg_utils.set_attribute(node, "fill", color)
        elif Tag.PATTERN_FILL_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.PATTERN_FILL_SETTING)
            logger.warning(f"Pattern fill is not supported yet: {setting}")
        elif Tag.GRADIENT_FILL_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.GRADIENT_FILL_SETTING)
            logger.warning(f"Gradient fill is not supported yet: {setting}")
        else:
            logger.debug(f"No fill information found: {layer}.")

    def set_stroke(self, layer: layers.Layer, node: ET.Element) -> None:
        """Add stroke style to the path node."""
        if not layer.has_stroke() or not layer.stroke.enabled:
            logger.debug("Layer has no stroke: %s", layer.name)
            return

        stroke = layer.stroke
        if stroke.line_alignment != "center":
            logger.warning("Inner or outer stroke is not supported yet.")
            # TODO: Perhaps use clipPath to simulate this.
        if stroke.line_width != 1.0:
            svg_utils.set_attribute(node, "stroke-width", stroke.line_width)

        if stroke.content.name == "patternoverlay":
            logger.warning("Pattern stroke is not supported yet.")
            # TODO: Implement pattern stroke.
        elif stroke.content.name == "gradientoverlay":
            logger.warning("Gradient stroke is not supported yet.")
            # TODO: Implement gradient stroke.
        elif stroke.content.classID == b"solidColorLayer":
            color = color_utils.descriptor2hex(stroke.content[Klass.Color])
            svg_utils.set_attribute(node, "stroke", color)

        if not stroke.fill_enabled:
            svg_utils.set_attribute(node, "fill", "transparent")

        if stroke.opacity.value < 100:
            svg_utils.set_attribute(
                node, "stroke-opacity", stroke.opacity.value / 100.0
            )

        if stroke.line_cap_type != "butt":
            svg_utils.set_attribute(node, "stroke-linecap", stroke.line_cap_type)
        if stroke.line_join_type != "miter":
            svg_utils.set_attribute(node, "stroke-linejoin", stroke.line_join_type)
        if stroke.line_dash_set:
            line_dash_set = [
                float(x.value) * stroke.line_width for x in stroke.line_dash_set
            ]
            svg_utils.set_attribute(node, "stroke-dasharray", line_dash_set)
            svg_utils.set_attribute(node, "stroke-dashoffset", stroke.line_dash_offset)
        # TODO: stroke blend mode?
