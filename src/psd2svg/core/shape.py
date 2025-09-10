import logging
import xml.etree.ElementTree as ET

from psd_tools.api import layers
from psd_tools.api.shape import VectorMask
from psd_tools.constants import Tag
from psd_tools.psd.descriptor import Descriptor
from psd_tools.terminology import Klass

from psd2svg.core import svg_utils
from psd2svg.core.base import ConverterProtocol
from psd2svg.utils.color import cmyk2rgb

logger = logging.getLogger(__name__)


class ShapeConverter(ConverterProtocol):
    """Mixin for shape layers."""

    def add_shape(self, layer: layers.ShapeLayer) -> ET.Element | None:
        """Add a shape layer to the svg document."""
        node = self.create_path(layer)
        if node is not None:
            self.set_fill(layer, node)
            self.set_stroke(layer, node)
        return node

    def add_fill(self, layer: layers.FillLayer) -> ET.Element | None:
        """Add fill node to the given element."""
        node = self.create_rect(layer)
        self.set_fill(layer, node)
        return node

    def create_path(self, layer: layers.Layer) -> ET.Element | None:
        """Create a path element."""
        if not layer.has_vector_mask():
            logger.warning("Layer has no vector mask: %s", layer.name)
            return None

        path = svg_utils.create_node(
            "path", parent=self.current, d=self.generate_path(layer.vector_mask)
        )
        if layer.vector_mask.initial_fill_rule:
            logger.warning("Initial fill rule (inverted mask) is not supported yet.")
        path.set("fill-rule", "evenodd")
        return path

    def generate_path(
        self: ConverterProtocol,
        vector_mask: VectorMask,
        command: str = "C",
        number_format: str = "%.2g",
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

    def create_rect(self, layer: layers.Layer) -> ET.Element:
        """Create a rectangle node."""
        viewbox = layer.bbox
        if viewbox == (0, 0, 0, 0):
            viewbox = (0, 0, self.psd.width, self.psd.height)
        return svg_utils.create_node(
            "rect",
            x=viewbox[0],
            y=viewbox[1],
            width=viewbox[2] - viewbox[0],
            height=viewbox[3] - viewbox[1],
        )

    def set_fill(self, layer: layers.Layer, node: ET.Element) -> None:
        """Set fill attribute to the given element."""

        if Tag.SOLID_COLOR_SHEET_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.SOLID_COLOR_SHEET_SETTING)
            color = self.create_solid_color(setting[Klass.Color])
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
                color = self.create_solid_color(content_data[Klass.Color])
                svg_utils.set_attribute(node, "fill", color)
            else:
                logger.warning(f"Unsupported fill content: {content_data}")

    def create_solid_color(self, color: Descriptor) -> str:
        """
        Create a fill attribute.

        This is supposed to be solidColor of SVG 1.2 Tiny spec, but for now,
        implement as fill attribute.

        :rtype: str
        """
        assert color is not None
        if color.classID == Klass.RGBColor:
            return "rgb(%g,%g,%g)" % tuple(map(int, color.values()))
        elif color.classID == Klass.Grayscale:
            return "rgb({0},{0},{0})".format([int(255 * x) for x in color.values()][0])
        elif color.classID == Klass.CMYKColor:
            return "rgb(%g,%g,%g)" % tuple(map(int, cmyk2rgb(color.values())))
        else:
            logger.warning(f"Unsupported color: {color}")
            return "transparent"

    def set_stroke(self, layer: layers.Layer, node: ET.Element) -> None:
        """Add stroke style to the path node."""
        if not layer.has_stroke() or not layer.stroke.enabled:
            return

        stroke = layer.stroke
        if stroke.line_alignment == "inner":
            clippath = svg_utils.create_node(
                "clipPath", parent=self.current, id=self.auto_id("clip_")
            )
            path = self.generate_path(layer.vector_mask)
            svg_utils.create_node("path", d=path, parent=clippath)
            svg_utils.set_attribute(node, "stroke-width", stroke.line_width * 2)
            svg_utils.set_attribute(node, "clip-path", svg_utils.get_funciri(clippath))

        elif stroke.line_alignment == "outer":
            logger.warning("Outer stroke is not supported yet.")
            # TODO: Implement outer stroke.
        else:
            svg_utils.set_attribute(node, "stroke-width", stroke.line_width)

        if stroke.content.name == "patternoverlay":
            logger.warning("Pattern stroke is not supported yet.")
            # TODO: Implement pattern stroke.
        elif stroke.content.name == "gradientoverlay":
            logger.warning("Gradient stroke is not supported yet.")
            # TODO: Implement gradient stroke.
        elif stroke.content.classID == b"solidColorLayer":
            svg_utils.set_attribute(
                node, "stroke", self.create_solid_color(stroke.content[Klass.Color])
            )

        if not stroke.fill_enabled:
            svg_utils.set_attribute(node, "fill", "transparent")

        svg_utils.set_attribute(node, "stroke-opacity", stroke.opacity.value / 100.0)
        svg_utils.set_attribute(node, "stroke-linecap", stroke.line_cap_type)
        svg_utils.set_attribute(node, "stroke-linejoin", stroke.line_join_type)
        if stroke.line_dash_set:
            svg_utils.set_attribute(
                node,
                "stroke-dasharray",
                ",".join(
                    [
                        str(float(x.value) * stroke.line_width)
                        for x in stroke.line_dash_set
                    ]
                ),
            )
            svg_utils.set_attribute(node, "stroke-dashoffset", stroke.line_dash_offset)
        # TODO: stroke blend mode?
