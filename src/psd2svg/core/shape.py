import contextlib
import logging
import xml.etree.ElementTree as ET
from typing import Iterator

from psd_tools.api import adjustments, layers
from psd_tools.api.shape import VectorMask, Rectangle, RoundedRectangle, Ellipse, Line
from psd_tools.constants import Tag
from psd_tools.terminology import Klass, Enum

from psd2svg.core import color_utils, svg_utils
from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class ShapeConverter(ConverterProtocol):
    """Mixin for shape layers."""

    def add_shape(self, layer: layers.ShapeLayer) -> ET.Element | None:
        """Add a shape layer to the svg document."""
        node = self._create_shape(layer)
        if node is not None:
            self.set_fill(layer, node)
            self.set_stroke(layer, node)
        return node

    def _create_shape(self, layer: layers.ShapeLayer) -> ET.Element | None:
        if layer.has_origination():
            if len(layer.origination) > 1:
                logger.warning("Multiple origination shapes are not supported yet.")
            shape = layer.origination[0]
            if isinstance(shape, Rectangle):
                node = svg_utils.create_node(
                    "rect",
                    parent=self.current,
                    x=shape.bbox[0],
                    y=shape.bbox[1],
                    width=shape.bbox[2] - shape.bbox[0],
                    height=shape.bbox[3] - shape.bbox[1],
                    title=layer.name,
                )
            elif isinstance(shape, RoundedRectangle):
                rx = (
                    float(shape.radii[b"topRight"]) + float(shape.radii[b"bottomRight"])
                ) / 2
                ry = (
                    float(shape.radii[b"topRight"]) + float(shape.radii[b"topLeft"])
                ) / 2
                node = svg_utils.create_node(
                    "rect",
                    parent=self.current,
                    x=shape.bbox[0],
                    y=shape.bbox[1],
                    width=shape.bbox[2] - shape.bbox[0],
                    height=shape.bbox[3] - shape.bbox[1],
                    rx=rx,
                    ry=ry,
                    title=layer.name,
                )
            elif isinstance(shape, Ellipse):
                cx = (shape.bbox[0] + shape.bbox[2]) / 2
                cy = (shape.bbox[1] + shape.bbox[3]) / 2
                rx = (shape.bbox[2] - shape.bbox[0]) / 2
                ry = (shape.bbox[3] - shape.bbox[1]) / 2
                node = svg_utils.create_node(
                    "ellipse",
                    parent=self.current,
                    cx=cx,
                    cy=cy,
                    rx=rx,
                    ry=ry,
                    title=layer.name,
                )
            # # Line shape is not supported, as this can be an arrow and fill is not applied.
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
                logger.debug(f"Unsupported shape type: {type(shape)}: {shape._data}")
                node = self.create_path(layer)
        else:
            node = self.create_path(layer)
        return node

    def add_fill(self, layer: adjustments.SolidColorFill) -> ET.Element | None:
        """Add fill node to the given element."""
        logger.debug(f"Adding fill layer: '{layer.name}'")
        viewbox = layer.bbox
        if viewbox == (0, 0, 0, 0):
            viewbox = (0, 0, self.psd.width, self.psd.height)
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

    @contextlib.contextmanager
    def add_clipping_target(self, layer: layers.Layer | layers.Group) -> Iterator[None]:
        """Context manager to handle clipping target."""
        parent = self.current
        if isinstance(layer, layers.ShapeLayer):
            self.current, path = self.add_clip_path(layer)
            yield
            self.current = parent
            self.add_clip_path_stroke(layer, path)
        else:
            self.current, target = self.add_clip_mask(layer)
            yield
            self.current = parent
            self.add_clip_mask_stroke(layer, target)

    def add_clip_path(self, layer: layers.ShapeLayer) -> tuple[ET.Element, ET.Element]:
        """Add a clipping path and associated elements."""

        # TODO: Support live shapes (layer origination).
        if not layer.has_vector_mask():
            raise ValueError("Layer has no vector mask: %s", layer.name)

        # Create a clipping path definition.
        clip_path = svg_utils.create_node(
            "clipPath", parent=self.current, id=self.auto_id("clip_")
        )

        parent = self.current
        self.current = clip_path
        shape = self._create_shape(layer)
        self.current = parent

        if shape is None:
            raise ValueError(
                "Failed to create clipping shape for layer: %s", layer.name
            )
        svg_utils.set_attribute(shape, "id", self.auto_id("shape_"))

        # Creeate a <use> element to reference the shape object for filling.
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(shape),
        )
        self.set_fill(layer, use)

        # Create a group with the clipping path applied.
        group = svg_utils.create_node("g", parent=self.current)
        svg_utils.set_attribute(group, "clip-path", svg_utils.get_funciri(clip_path))
        return group, shape

    def add_clip_path_stroke(self, layer: layers.ShapeLayer, shape: ET.Element) -> None:
        """Add stroke to the clipping path."""
        # Creeate a <use> element to reference the shape object for stroke effect.
        if not layer.has_stroke() or not layer.stroke.enabled:
            return

        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(shape),
        )
        svg_utils.set_attribute(use, "fill", "transparent")
        self.set_stroke(layer, use)

    def add_clip_mask(
        self, layer: layers.Layer | layers.Group
    ) -> tuple[ET.Element, ET.Element]:
        """Add a clipping mask and associated elements."""

        # Create a clipping mask definition.
        mask = svg_utils.create_node(
            "mask", parent=self.current, id=self.auto_id("mask_")
        )
        svg_utils.set_attribute(mask, "mask-type", "alpha")
        parent = self.current
        self.current = mask
        target = self.add_layer(layer)
        self.current = parent
        if target is None:
            raise ValueError(
                "Failed to create clipping target for layer: %s", layer.name
            )
        if "id" not in target.attrib:
            target.set("id", self.auto_id("cliptarget_"))

        # Create a <use> element to reference the target object.
        svg_utils.create_node(
            "use", parent=self.current, href=svg_utils.get_uri(target)
        )

        # Create a group with the clipping mask applied.
        group = svg_utils.create_node(
            "g", parent=self.current, mask=svg_utils.get_funciri(mask)
        )
        return group, target

    def add_clip_mask_stroke(
        self, layer: layers.Layer | layers.Group, target: ET.Element
    ) -> None:
        """Add stroke effect to the clipping mask target."""
        # Creeate a <use> element to reference the target object for stroke effect.
        if not layer.has_effects():
            return
        for effect in layer.effects.find("stroke"):
            if not effect.enabled:
                continue

            filter = self.add_stroke_filter(effect)
            svg_utils.create_node(
                "use",
                parent=self.current,
                href=svg_utils.get_uri(target),
                filter=svg_utils.get_funciri(filter),
            )

    def create_path(self, layer: layers.Layer) -> ET.Element:
        """Create a path element."""
        if not layer.has_vector_mask():
            raise ValueError("Layer has no vector mask: %s", layer.name)

        path = svg_utils.create_node(
            "path",
            parent=self.current,
            d=self.generate_path(layer.vector_mask),
            title=layer.name,
        )
        if layer.vector_mask.initial_fill_rule:
            logger.warning("Initial fill rule (inverted mask) is not supported yet.")
        # svg_utils.set_attribute(path, "fill-rule", "evenodd")
        return path

    def generate_path(
        self: ConverterProtocol,
        vector_mask: VectorMask,
        command: str = "C",
        number_format: str = "%g",
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
                yield (number_format + "," + number_format) % (
                    path[0].anchor[1] * self.psd.width,
                    path[0].anchor[0] * self.psd.height,
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
                    yield (number_format + "," + number_format) % (
                        p1.leaving[1] * self.psd.width,
                        p1.leaving[0] * self.psd.height,
                    )
                    yield (number_format + "," + number_format) % (
                        p2.preceding[1] * self.psd.width,
                        p2.preceding[0] * self.psd.height,
                    )
                    yield (number_format + "," + number_format) % (
                        p2.anchor[1] * self.psd.width,
                        p2.anchor[0] * self.psd.height,
                    )

                if path.is_closed():
                    yield "Z"

        return " ".join(str(x) for x in _do_generate())

    def set_fill(self, layer: layers.Layer, node: ET.Element) -> None:
        """Set fill attribute to the given element."""

        if Tag.SOLID_COLOR_SHEET_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.SOLID_COLOR_SHEET_SETTING)
            color = color_utils.descriptor2hex(setting[Klass.Color])
            svg_utils.set_attribute(node, "fill", color)
        elif Tag.PATTERN_FILL_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.PATTERN_FILL_SETTING)
            logger.warning(f"Pattern fill is not supported yet: {setting}")
        elif Tag.GRADIENT_FILL_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.GRADIENT_FILL_SETTING)
            logger.warning(f"Gradient fill is not supported yet: {setting}")
        elif Tag.VECTOR_STROKE_CONTENT_DATA in layer.tagged_blocks:
            content_data = layer.tagged_blocks.get_data(Tag.VECTOR_STROKE_CONTENT_DATA)
            if Klass.Color in content_data:
                color = color_utils.descriptor2hex(content_data[Klass.Color])
                svg_utils.set_attribute(node, "fill", color)
            else:
                logger.warning(f"Unsupported fill content: {content_data}")

    def set_stroke(self, layer: layers.Layer, node: ET.Element) -> None:
        """Add stroke style to the path node."""
        if not layer.has_stroke() or not layer.stroke.enabled:
            return

        stroke = layer.stroke
        if stroke.line_alignment != "center":
            logger.warning("Inner or outer stroke is not supported yet.")
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
