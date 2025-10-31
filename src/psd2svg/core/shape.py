import logging
import xml.etree.ElementTree as ET
from typing import Iterator, Literal

import numpy as np
from psd_tools import PSDImage
from psd_tools.api import adjustments, layers, pil_io
from psd_tools.api.shape import Ellipse, Rectangle, RoundedRectangle
from psd_tools.constants import Tag
from psd_tools.psd.descriptor import Descriptor
from psd_tools.psd.vector import Subpath
from psd_tools.terminology import Enum, Key, Klass, Unit

from psd2svg import svg_utils
from psd2svg.core import color_utils
from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class ShapeConverter(ConverterProtocol):
    """Mixin for shape layers."""

    def create_shape(self, layer: layers.ShapeLayer, **attrib) -> ET.Element:
        """Create a shape element from the layer's vector mask or origination data."""
        if not layer.has_vector_mask():
            raise ValueError(f"Layer has no vector mask: '{layer.name}' ({layer.kind})")

        if len(layer.vector_mask.paths) == 1:
            # TODO: Handle NOT OR for single path.
            path = layer.vector_mask.paths[0]
            return self.create_single_shape(layer, path, **attrib)

        # Group subpaths by operations.
        subpaths: list[list[Subpath]] = []
        for path in layer.vector_mask.paths:
            if path.operation == -1:  # Even-odd fill rule
                if len(subpaths) == 0:
                    logger.warning("Even-odd fill rule without preceding path")
                    subpaths.append([path])
                else:
                    subpaths[-1].append(path)
            else:
                subpaths.append([path])

        rule: Literal["fill-rule", "clip-rule"] = (
            "clip-rule" if self.current.tag == "clipPath" else "fill-rule"
        )

        # TODO: Use clipPath when possible.
        # Composite shape with multiple paths.
        current = svg_utils.create_node(
            "mask",
            parent=self.current,
            id=self.auto_id("mask"),
        )
        for path_group in subpaths:
            path = path_group[0]
            previous = current
            if path.operation == 0:  # XOR
                current = self.apply_xor_operation(
                    layer, path_group, current, previous, rule
                )
            elif path.operation == 1:  # Union (OR)
                current = self.apply_union_operation(layer, path_group, current, rule)
            elif path.operation == 2:  # Subtract (NOT OR)
                current = self.apply_subtract_operation(
                    layer, path_group, current, rule
                )
            elif path.operation == 3:  # Intersect (AND)
                current = self.apply_intersect_operation(
                    layer, path_group, current, previous, rule
                )
            else:
                raise ValueError(f"Unsupported path operation: {path.operation}")

        return svg_utils.create_node(
            "rect",
            parent=self.current,
            x=layer.left,
            y=layer.top,
            width=layer.width,
            height=layer.height,
            mask=svg_utils.get_funciri(current),
            **attrib,
        )

    def apply_union_operation(
        self,
        layer: layers.ShapeLayer,
        path_group: list[Subpath],
        current: ET.Element,
        rule: Literal["fill-rule", "clip-rule"],
    ) -> ET.Element:
        """Apply Union (OR) operation to combine shapes."""
        with self.set_current(current):
            # Union operation: add the shape directly.
            if len(path_group) > 1:
                self.create_composite_path(path_group, rule, fill="#ffffff")
            else:
                self.create_single_shape(layer, path_group[0], fill="#ffffff")
        return current

    def apply_subtract_operation(
        self,
        layer: layers.ShapeLayer,
        path_group: list[Subpath],
        current: ET.Element,
        rule: Literal["fill-rule", "clip-rule"],
    ) -> ET.Element:
        """Apply Subtract (NOT OR) operation to create holes."""
        with self.set_current(current):
            if len(current) == 0:
                # First shape: fill white.
                svg_utils.create_node(
                    "rect", fill="#ffffff", width="100%", height="100%"
                )
            # Subtract (Make a hole).
            if len(path_group) > 1:
                self.create_composite_path(path_group, rule, fill="#000000")
            else:
                self.create_single_shape(layer, path_group[0], fill="#000000")
        return current

    def apply_intersect_operation(
        self,
        layer: layers.ShapeLayer,
        path_group: list[Subpath],
        current: ET.Element,
        previous: ET.Element,
        rule: Literal["fill-rule", "clip-rule"],
    ) -> ET.Element:
        """Apply Intersect (AND) operation to find overlapping regions."""
        # Create a new mask for the AND operation.
        if len(previous) > 0:
            current = svg_utils.create_node(
                "mask",
                parent=self.current,
                id=self.auto_id("mask"),
            )
        with self.set_current(current):
            # Create the intersection by masking the previous shape.
            if len(path_group) > 1:
                self.create_composite_path(path_group, rule, fill="#ffffff")
            else:
                self.create_single_shape(
                    layer,
                    path_group[0],
                    mask=svg_utils.get_funciri(previous)
                    if len(previous) > 0
                    else None,
                    fill="#ffffff",
                )
        return current

    def apply_xor_operation(
        self,
        layer: layers.ShapeLayer,
        path_group: list[Subpath],
        current: ET.Element,
        previous: ET.Element,
        rule: Literal["fill-rule", "clip-rule"],
    ) -> ET.Element:
        """Apply XOR (exclusive-or) operation using (A OR B) AND NOT (A AND B)."""
        if len(previous) == 0:
            # First shape: just add it directly (XOR with nothing = identity)
            with self.set_current(current):
                if len(path_group) > 1:
                    self.create_composite_path(path_group, rule, fill="#ffffff")
                else:
                    self.create_single_shape(layer, path_group[0], fill="#ffffff")
            return current

        # Create the shape in <defs> to reuse it
        defs = svg_utils.create_node("defs", parent=self.current)
        shape_id = self.auto_id("shape")
        with self.set_current(defs):
            if len(path_group) > 1:
                self.create_composite_path(path_group, rule, id=shape_id)
            else:
                self.create_single_shape(layer, path_group[0], id=shape_id)

        # Create a mask for the union (A OR B)
        union_mask = svg_utils.create_node(
            "mask",
            parent=self.current,
            id=self.auto_id("mask"),
        )
        # Add previous shapes to union
        with self.set_current(union_mask):
            svg_utils.create_node(
                "rect",
                parent=self.current,
                fill="#ffffff",
                width="100%",
                height="100%",
                mask=svg_utils.get_funciri(previous),
            )
        # Add current shape to union using <use>
        with self.set_current(union_mask):
            svg_utils.create_node(
                "use",
                parent=self.current,
                href=f"#{shape_id}",
                fill="#ffffff",
            )

        # Create a mask for the intersection (A AND B)
        intersection_mask = svg_utils.create_node(
            "mask",
            parent=self.current,
            id=self.auto_id("mask"),
        )
        with self.set_current(intersection_mask):
            svg_utils.create_node(
                "use",
                parent=self.current,
                href=f"#{shape_id}",
                fill="#ffffff",
                mask=svg_utils.get_funciri(previous),
            )

        # Create the final XOR mask: union minus intersection
        current = svg_utils.create_node(
            "mask",
            parent=self.current,
            id=self.auto_id("mask"),
        )
        with self.set_current(current):
            # Add the union
            svg_utils.create_node(
                "rect",
                parent=self.current,
                fill="#ffffff",
                width="100%",
                height="100%",
                mask=svg_utils.get_funciri(union_mask),
            )
            # Subtract the intersection
            svg_utils.create_node(
                "rect",
                parent=self.current,
                fill="#000000",
                width="100%",
                height="100%",
                mask=svg_utils.get_funciri(intersection_mask),
            )
        return current

    def create_single_shape(
        self, layer: layers.ShapeLayer, path: Subpath, **attrib
    ) -> ET.Element:
        """Create a single shape element from the layer's vector mask or origination data."""
        if not layer.has_vector_mask():
            raise ValueError("Layer has no vector mask: %s", layer.name)

        if layer.vector_mask.initial_fill_rule:
            logger.warning("Initial fill rule (inverted mask) is not supported yet.")

        if layer.has_origination():
            origination = layer.origination[path.index]
            reference = layer.tagged_blocks.get_data(Tag.REFERENCE_POINT, (0.0, 0.0))
            if isinstance(origination, Rectangle):
                node = self.create_origination_rectangle(
                    origination, reference, **attrib
                )
                self.set_origination_transform(layer, origination, node)
            elif isinstance(origination, RoundedRectangle):
                node = self.create_origination_rounded_rectangle(
                    origination, reference, **attrib
                )
                self.set_origination_transform(layer, origination, node)
            elif isinstance(origination, Ellipse):
                node = self.create_origination_ellipse(origination, reference, **attrib)
                self.set_origination_transform(layer, origination, node)
            else:
                # Fallback to path creation.
                # TODO: Support line shapes.
                logger.debug(f"Unsupported shape type: {origination}")
                node = self.create_path(path, **attrib)
        else:
            node = self.create_path(path, **attrib)

        return node

    def create_origination_rectangle(
        self,
        origination: Rectangle,
        reference: tuple[float, float],
        **attrib,
    ) -> ET.Element:
        """Create a rectangle shape from origination data."""
        bbox = get_origin_bbox(origination, reference)
        return svg_utils.create_node(
            "rect",
            parent=self.current,
            x=bbox[0],
            y=bbox[1],
            width=bbox[2] - bbox[0],
            height=bbox[3] - bbox[1],
            **attrib,
        )

    def create_origination_rounded_rectangle(
        self,
        origination: RoundedRectangle,
        reference: tuple[float, float],
        **attrib,
    ) -> ET.Element:
        """Create a rounded rectangle shape from origination data."""
        bbox = get_origin_bbox(origination, reference)
        scales = get_origin_scale(origination)
        scale = (scales[0] + scales[1]) / 2
        rx = (
            (
                float(origination.radii[b"topRight"])
                + float(origination.radii[b"bottomRight"])
            )
            / 2
            / scale
        )
        ry = (
            (
                float(origination.radii[b"topRight"])
                + float(origination.radii[b"topLeft"])
            )
            / 2
            / scale
        )
        return svg_utils.create_node(
            "rect",
            parent=self.current,
            x=bbox[0],
            y=bbox[1],
            width=bbox[2] - bbox[0],
            height=bbox[3] - bbox[1],
            rx=rx,
            ry=ry,
            **attrib,
        )

    def create_origination_ellipse(
        self, origination: Ellipse, reference: tuple[float, float], **attrib
    ) -> ET.Element:
        """Create an ellipse shape from origination data."""
        bbox = get_origin_bbox(origination, reference)
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        rx = (bbox[2] - bbox[0]) / 2
        ry = (bbox[3] - bbox[1]) / 2
        if rx == ry:
            return svg_utils.create_node(
                "circle",
                parent=self.current,
                cx=int(cx),
                cy=int(cy),
                r=rx,
                **attrib,
            )
        else:
            return svg_utils.create_node(
                "ellipse",
                parent=self.current,
                cx=int(cx),
                cy=int(cy),
                rx=rx,
                ry=ry,
                **attrib,
            )

    def set_origination_transform(
        self,
        layer: layers.ShapeLayer,
        origination: Rectangle | RoundedRectangle | Ellipse,
        node: ET.Element,
    ) -> None:
        """Set transform attribute from origination data."""
        # Check if transform is available.
        if b"Trnf" not in origination._data:
            return

        # Apply the transformation matrix.
        transform = origination._data[b"Trnf"]
        assert transform.classID == b"Trnf"
        matrix = (
            float(transform[b"xx"]),
            float(transform[b"xy"]),
            float(transform[b"yx"]),
            float(transform[b"yy"]),
            float(transform[b"tx"]),
            float(transform[b"ty"]),
        )
        if matrix != (1, 0, 0, 1, 0, 0):
            svg_utils.append_attribute(
                node,
                "transform",
                "matrix(%s)" % svg_utils.seq2str(matrix, format=".3f"),
            )

        # Adjust the offset by the reference point.
        reference = tuple(layer.tagged_blocks.get_data(Tag.REFERENCE_POINT, (0, 0)))
        if reference != (0.0, 0.0):
            svg_utils.append_attribute(
                node,
                "transform",
                "translate(%s)"
                % svg_utils.seq2str((-reference[0], -reference[1]), format=".3f"),
            )

    def create_path(self, path: Subpath, **attrib) -> ET.Element:
        """Create a path element."""
        return svg_utils.create_node(
            "path",
            parent=self.current,
            d=" ".join(generate_path(path, self.psd.width, self.psd.height)),
            **attrib,
        )

    def create_composite_path(
        self,
        paths: list[Subpath],
        rule: Literal["fill-rule", "clip-rule"] = "fill-rule",
        **attrib,
    ) -> ET.Element:
        """Create a composite path element."""
        return svg_utils.create_node(
            "path",
            parent=self.current,
            d=" ".join(
                " ".join(generate_path(path, self.psd.width, self.psd.height))
                for path in paths
            ),
            **{str(rule): "evenodd"},
            **attrib,
        )

    def apply_vector_fill(
        self, layer: layers.ShapeLayer | adjustments.FillLayer, target: ET.Element
    ) -> None:
        """Apply fill effects to the target element."""
        if layer.has_stroke() and not layer.stroke.fill_enabled:
            logger.debug(f"Fill is disabled for layer: '{layer.name}'")
            return

        use = svg_utils.create_node(
            "use", parent=self.current, href=svg_utils.get_uri(target)
        )
        self.set_fill(layer, use)
        self.set_blend_mode(layer.blend_mode, use)

    def apply_vector_stroke(
        self, layer: layers.ShapeLayer | adjustments.FillLayer, target: ET.Element
    ) -> None:
        """Apply stroke effects to the target element."""
        if not layer.has_stroke() or not layer.stroke.enabled:
            logger.debug(f"Layer has no stroke: '{layer.name}'")
            return

        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            fill="transparent",
        )
        self.set_stroke(layer, use)
        # TODO: Check if we already set stroke.

    def set_fill(
        self, layer: layers.ShapeLayer | adjustments.FillLayer, node: ET.Element
    ) -> None:
        """Set fill attribute to the given element."""
        # Transparent fill when stroke is enabled but fill is disabled.
        if layer.has_stroke() and not layer.stroke.fill_enabled:
            logger.debug("Fill is disabled; setting fill to transparent.")
            svg_utils.set_attribute(node, "fill", "transparent")
            return

        # Shapes have the following tagged blocks for fill content.
        if Tag.VECTOR_STROKE_CONTENT_DATA in layer.tagged_blocks:
            self.set_fill_stroke_content(layer, node)
            return

        # Fill layers have a dedicated tagged block.
        self.set_fill_setting(layer, node)

    def set_fill_stroke_content(
        self, layer: layers.ShapeLayer, node: ET.Element
    ) -> None:
        """Set fill or stroke content from VECTOR_STROKE_CONTENT_DATA."""
        content_data = layer.tagged_blocks.get_data(Tag.VECTOR_STROKE_CONTENT_DATA)
        if Key.Color in content_data:
            color = color_utils.descriptor2hex(content_data[Key.Color])
            svg_utils.set_attribute(node, "fill", color)
        elif Key.Gradient in content_data:
            gradient = self.add_gradient_definition(content_data)
            if gradient is not None:
                svg_utils.set_attribute(node, "fill", svg_utils.get_funciri(gradient))
        else:
            logger.warning(f"Unsupported fill content: {content_data}")
        self.set_fill_opacity(layer, node)

    def set_fill_setting(self, layer: adjustments.FillLayer, node: ET.Element) -> None:
        """Set fill attribute from fill settings tagged blocks."""
        if Tag.SOLID_COLOR_SHEET_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.SOLID_COLOR_SHEET_SETTING)
            color = color_utils.descriptor2hex(setting[Klass.Color])
            svg_utils.set_attribute(node, "fill", color)
        elif Tag.PATTERN_FILL_SETTING in layer.tagged_blocks:
            # classID is null for pattern fill setting.
            setting = layer.tagged_blocks.get_data(Tag.PATTERN_FILL_SETTING)
            if Enum.Pattern not in setting:
                raise ValueError(f"No pattern found in setting: {setting}.")
            pattern = self.add_pattern(self.psd, setting[Enum.Pattern])
            if pattern is not None:
                svg_utils.set_attribute(node, "fill", svg_utils.get_funciri(pattern))
        elif Tag.GRADIENT_FILL_SETTING in layer.tagged_blocks:
            # classID is null for gradient fill setting.
            setting = layer.tagged_blocks.get_data(Tag.GRADIENT_FILL_SETTING)
            gradient = self.add_gradient_definition(setting)
            if gradient is not None:
                svg_utils.set_attribute(node, "fill", svg_utils.get_funciri(gradient))
        else:
            logger.debug(f"No fill information found: {layer}.")
        self.set_fill_opacity(layer, node)

    def set_fill_opacity(self, layer: layers.Layer, node: ET.Element) -> None:
        """Set fill opacity to the given element."""
        fill_opacity = layer.tagged_blocks.get_data(Tag.BLEND_FILL_OPACITY, 255) / 255.0
        if fill_opacity < 1.0:
            svg_utils.set_attribute(node, "fill-opacity", fill_opacity)

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

    def add_gradient_definition(self, descriptor: Descriptor) -> ET.Element | None:
        """Add gradient definition to the SVG document."""
        if descriptor[Key.Type].enum == Enum.Linear:
            node = self.add_linear_gradient(descriptor[Key.Gradient])
        elif descriptor[Key.Type].enum == Enum.Radial:
            node = self.add_radial_gradient(descriptor[Key.Gradient])
        else:
            logger.warning("Only linear and radial gradients are supported yet.")
            return None
        self.set_gradient_attributes(descriptor, node)
        return node

    def add_linear_gradient(self, gradient: Descriptor) -> ET.Element:
        """Add linear gradient definition to the SVG document."""
        node = svg_utils.create_node(
            "linearGradient", parent=self.current, id=self.auto_id("gradient")
        )
        self.set_gradient_stops(gradient, node)
        return node

    def add_radial_gradient(self, gradient: Descriptor) -> ET.Element:
        """Add radial gradient definition to the SVG document."""
        node = svg_utils.create_node(
            "radialGradient", parent=self.current, id=self.auto_id("gradient")
        )
        self.set_gradient_stops(gradient, node)
        return node

    def set_gradient_stops(self, gradient: Descriptor, node: ET.Element) -> ET.Element:
        """Set gradient stops to the given gradient element."""
        assert gradient.classID == Klass.Gradient

        # Insert color and opacity stops.
        color_stops = {
            int(stop[Key.Location]): stop[Key.Color] for stop in gradient[Key.Colors]
        }
        opacity_stops = {
            int(stop[Key.Location]): stop[Key.Opacity]
            for stop in gradient[Key.Transparency]
        }
        stop_keys = set(color_stops.keys()) | set(opacity_stops.keys())
        for location in sorted(stop_keys):
            offset = location / 4096.0
            if location not in color_stops:
                logger.debug(f"No color stop found at location: {location}")
                stop_color = None
                # TODO: Get interpolated color
            else:
                stop_color = color_utils.descriptor2hex(color_stops[location])
            if location not in opacity_stops:
                logger.debug(f"No opacity stop found at location: {location}")
                # TODO: Get interpolated opacity
            else:
                stop_opacity = opacity_stops[location] / 100.0

            svg_utils.create_node(
                "stop",
                parent=node,
                offset=f"{offset:.0%}",
                stop_color=stop_color,
                stop_opacity=stop_opacity,
            )

        # TODO: Midpoint support?
        if any(stop[Key.Midpoint] != 50 for stop in gradient[Key.Colors]) or any(
            stop[Key.Midpoint] != 50 for stop in gradient[Key.Transparency]
        ):
            logger.debug("Gradient midpoint is not supported.")

        return node

    def set_gradient_attributes(
        self, setting: Descriptor, gradient: ET.Element
    ) -> None:
        """Set gradient settings such as angle to the gradient element."""
        if Key.Angle in setting:
            angle = setting[Key.Angle]
            if angle.unit != Unit.Angle:
                logger.warning(f"Unsupported angle unit: {angle.unit}")
            if angle.value != 0:
                logger.info(f"Rotation angle != 0 might be inaccurate: {angle.value}")
                # TODO: Support rotation for uneven aspect ratio.
                rotation = -angle.value
                svg_utils.set_attribute(
                    gradient,
                    "gradientTransform",
                    f"translate(0.5 0.5) rotate({rotation:.0f}) translate(-0.5 -0.5)",
                )

    def add_pattern(self, psdimage: PSDImage, descriptor: Descriptor) -> ET.Element:
        """Add pattern definition to the SVG document."""
        assert descriptor.classID == Enum.Pattern
        pattern_id = descriptor[Key.ID].value.rstrip("\x00")
        pattern_data = psdimage._get_pattern(pattern_id)
        if pattern_data is None:
            raise ValueError(f"Pattern data not found: {pattern_id}")
        image = pil_io.convert_pattern_to_pil(pattern_data)

        node = svg_utils.create_node(
            "pattern",
            parent=self.current,
            id=self.auto_id("pattern"),
            width=image.width,
            height=image.height,
            patternUnits="userSpaceOnUse",
        )
        svg_utils.create_node(
            "image", parent=node, width=image.width, height=image.height
        )
        # We will later fill in the href attribute when embedding images.
        self.images.append(image)
        return node


def generate_path(
    path: Subpath, width: int, height: int, command: str = "C"
) -> Iterator[str]:
    """Sequence generator for SVG path constructor."""
    if len(path) == 0:
        return

    # Initial point.
    yield "M"
    yield ",".join(
        [
            svg_utils.num2str(path[0].anchor[1] * width),
            svg_utils.num2str(path[0].anchor[0] * height),
        ]
    )

    # Closed path or open path
    points = (
        zip(path, path[1:] + path[0:1]) if path.is_closed() else zip(path, path[1:])
    )

    # Rest of the points.
    yield command
    for p1, p2 in points:
        yield ",".join(
            [
                svg_utils.num2str(p1.leaving[1] * width),
                svg_utils.num2str(p1.leaving[0] * height),
            ]
        )
        yield ",".join(
            [
                svg_utils.num2str(p2.preceding[1] * width),
                svg_utils.num2str(p2.preceding[0] * height),
            ]
        )
        yield ",".join(
            [
                svg_utils.num2str(p2.anchor[1] * width),
                svg_utils.num2str(p2.anchor[0] * height),
            ]
        )

    if path.is_closed():
        yield "Z"


def get_origin_bbox(
    origination: Rectangle | RoundedRectangle | Ellipse,
    reference: tuple[float, float],
) -> tuple[float, float, float, float]:
    """Get the origin bounding box for origination data."""
    if b"keyOriginBoxCorners" in origination._data and b"Trnf" in origination._data:
        # Calculate rectangle from corner points when transform is available.
        # Corners are given in transformed space; i.e., after applying Trnf.
        corners = origination._data[b"keyOriginBoxCorners"]
        x1 = float(corners[b"rectangleCornerA"][b"Hrzn"])
        y1 = float(corners[b"rectangleCornerA"][b"Vrtc"])
        x2 = float(corners[b"rectangleCornerB"][b"Hrzn"])
        y2 = float(corners[b"rectangleCornerB"][b"Vrtc"])
        x3 = float(corners[b"rectangleCornerC"][b"Hrzn"])
        y3 = float(corners[b"rectangleCornerC"][b"Vrtc"])
        x4 = float(corners[b"rectangleCornerD"][b"Hrzn"])
        y4 = float(corners[b"rectangleCornerD"][b"Vrtc"])
        transform = origination._data[b"Trnf"]
        xx = float(transform[b"xx"])
        xy = float(transform[b"xy"])
        yx = float(transform[b"yx"])
        yy = float(transform[b"yy"])
        tx = float(transform[b"tx"])
        ty = float(transform[b"ty"])
        # Corners are in transformed space. Invert to get original coordinates.
        X = np.array([[x1, y1, 1], [x2, y2, 1], [x3, y3, 1], [x4, y4, 1]]).T
        M = np.array([[xx, yx, tx], [xy, yy, ty], [0, 0, 1]])
        # Apply inverse transform: Y = M^-1 @ X, then offset by reference point
        Y = np.linalg.solve(M, X) + np.array([[reference[0]], [reference[1]], [0]])
        bbox = (
            float(np.min(Y[0, :])),
            float(np.min(Y[1, :])),
            float(np.max(Y[0, :])),
            float(np.max(Y[1, :])),
        )
    else:
        bbox = origination.bbox
    return bbox


def get_origin_scale(
    origination: Rectangle | RoundedRectangle | Ellipse,
) -> tuple[float, float]:
    """Get the origin scale for origination data."""
    if b"Trnf" in origination._data:
        transform = origination._data[b"Trnf"]
        xx = float(transform[b"xx"])
        xy = float(transform[b"xy"])
        yx = float(transform[b"yx"])
        yy = float(transform[b"yy"])
        scale_x = (xx**2 + yx**2) ** 0.5
        scale_y = (xy**2 + yy**2) ** 0.5
        return (scale_x, scale_y)
    return (1.0, 1.0)
