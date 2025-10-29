import contextlib
import logging
import xml.etree.ElementTree as ET
from typing import Iterator

import numpy as np
from psd_tools.api import adjustments, layers
from psd_tools.api.shape import Rectangle, RoundedRectangle, Ellipse
from psd_tools.psd.descriptor import Descriptor
from psd_tools.psd.vector import Subpath
from psd_tools.constants import Tag
from psd_tools.terminology import Klass, Key, Enum, Unit

from psd2svg.core import color_utils
from psd2svg.core.base import ConverterProtocol
from psd2svg import svg_utils

logger = logging.getLogger(__name__)


class ShapeConverter(ConverterProtocol):
    """Mixin for shape layers."""

    def add_shape(self, layer: layers.ShapeLayer) -> ET.Element | None:
        """Add a shape layer to the svg document."""
        if layer.has_effects():
            # We need to split the shape definition and effects.
            defs = svg_utils.create_node("defs", parent=self.current)
            with self.set_current(defs):
                node = self.create_shape(
                    layer,
                    title=layer.name,
                    id=self.auto_id("shape"),
                )

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
            use = self.apply_vector_fill(layer, node)  # main filled shape.
            self.apply_overlay_effects(layer, node)
            self.apply_vector_stroke(layer, node)  # main stroke.
            self.apply_stroke_effect(layer, node)
            self.set_layer_attributes(layer, use)
        else:
            node = self.create_shape(layer, title=layer.name)
            self.set_fill(layer, node)
            self.set_stroke(layer, node)
            self.set_layer_attributes(layer, node)
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
                    id=self.auto_id("fill"),
                    title=layer.name,
                )
            self.apply_background_effects(layer, node, insert_before_target=False)
            use = self.apply_vector_fill(layer, node)  # main filled shape.
            self.apply_overlay_effects(layer, node)
            self.apply_vector_stroke(layer, node)
            self.apply_stroke_effect(layer, node)
            self.set_layer_attributes(layer, use)
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
            self.set_layer_attributes(layer, node)
        return node

    def create_shape(self, layer: layers.ShapeLayer, **attrib) -> ET.Element:
        """Create a shape element from the layer's vector mask or origination data."""
        if not layer.has_vector_mask():
            raise ValueError("Layer has no vector mask: %s", layer.name)

        if len(layer.vector_mask.paths) == 1:
            # TODO: Handle NOT OR for single path.
            path = layer.vector_mask.paths[0]
            return self.create_single_shape(layer, path, **attrib)

        # Composite shape with multiple paths.
        current = svg_utils.create_node(
            "mask",
            parent=self.current,
            id=self.auto_id("mask"),
        )
        for path in layer.vector_mask.paths:
            previous = current
            if path.operation == 1:  # OR
                with self.set_current(current):
                    # Union operation: add the shape directly.
                    self.create_single_shape(layer, path, fill="#ffffff")

            elif path.operation == 2:  # Subtract (NOT OR)
                with self.set_current(current):
                    if len(current) == 0:
                        # First shape: fill white.
                        svg_utils.create_node(
                            "rect", fill="#ffffff", width="100%", height="100%"
                        )
                    # Subtract (Make a hole).
                    self.create_single_shape(layer, path, fill="#000000")

            elif path.operation == 3:  # AND
                # Create a new mask for the AND operation.
                if len(previous) > 0:
                    current = svg_utils.create_node(
                        "mask",
                        parent=self.current,
                        id=self.auto_id("mask"),
                    )
                with self.set_current(current):
                    # Create the intersection by masking the previous shape.
                    self.create_single_shape(
                        layer,
                        path,
                        mask=svg_utils.get_funciri(previous)
                        if len(previous) > 0
                        else None,
                        fill="#ffffff",
                    )

            elif path.operation == 4:  # XOR
                logger.warning("XOR operation is not supported yet.")
            else:
                logger.error(f"Unknown path operation: {path.operation}")

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
        if not layer.has_vector_mask():
            raise ValueError("Layer has no vector mask: %s", layer.name)

        # Create a clipping path definition.
        clip_path = svg_utils.create_node(
            "clipPath", parent=self.current, id=self.auto_id("clip")
        )
        with self.set_current(clip_path):
            target = self.create_shape(
                layer, title=layer.name, id=self.auto_id("shape")
            )

        self.apply_background_effects(layer, target, insert_before_target=False)
        use = self.apply_vector_fill(layer, target)  # main filled shape.
        self.apply_overlay_effects(layer, target)
        # Create a group with the clipping path applied.
        group = svg_utils.create_node(
            "g", parent=self.current, clip_path=svg_utils.get_funciri(clip_path)
        )
        with self.set_current(group):
            yield  # Yield to the context block.

        # TODO: Inner filter effects on clipping path.
        self.apply_vector_stroke(layer, target)
        self.apply_stroke_effect(layer, target)
        self.set_layer_attributes(layer, use)

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
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            fill="transparent",
        )
        self.set_stroke(layer, use)
        # TODO: Check if we already set stroke.

    @contextlib.contextmanager
    def add_clip_mask(self, layer: layers.Layer | layers.Group) -> Iterator[None]:
        """Add a clipping mask and associated elements."""

        # Create a clipping mask definition.
        mask = svg_utils.create_node(
            "mask", parent=self.current, id=self.auto_id("mask"), mask_type="alpha"
        )
        with self.set_current(mask):
            target = self.add_layer(layer)

        if target is None:
            raise ValueError(
                "Failed to create clipping target for layer: %s", layer.name
            )
        if "id" not in target.attrib:
            target.set("id", self.auto_id("cliptarget"))

        self.apply_background_effects(layer, target, insert_before_target=False)
        # Create a <use> element to reference the target object.
        use = svg_utils.create_node(
            "use", parent=self.current, href=svg_utils.get_uri(target)
        )
        self.apply_overlay_effects(layer, target)

        # Create a group with the clipping mask applied.
        group = svg_utils.create_node(
            "g", parent=self.current, mask=svg_utils.get_funciri(mask)
        )
        with self.set_current(group):
            yield  # Yield to the context block.

        self.apply_stroke_effect(layer, target)
        self.set_layer_attributes(layer, use)

    def set_fill(self, layer: layers.Layer, node: ET.Element) -> None:
        """Set fill attribute to the given element."""
        # Transparent fill when stroke is enabled but fill is disabled.
        if layer.has_stroke() and not layer.stroke.fill_enabled:
            svg_utils.set_attribute(node, "fill", "transparent")
            return

        # Shapes have the following tagged blocks for fill content.
        if Tag.VECTOR_STROKE_CONTENT_DATA in layer.tagged_blocks:
            content_data = layer.tagged_blocks.get_data(Tag.VECTOR_STROKE_CONTENT_DATA)
            if Key.Color in content_data:
                color = color_utils.descriptor2hex(content_data[Key.Color])
                svg_utils.set_attribute(node, "fill", color)
            elif Key.Gradient in content_data:
                gradient = self.add_gradient_definition(content_data)
                if gradient is not None:
                    svg_utils.set_attribute(
                        node, "fill", svg_utils.get_funciri(gradient)
                    )
            else:
                logger.warning(f"Unsupported fill content: {content_data}")
            return

        # Fill layers have the following tagged blocks.
        if Tag.SOLID_COLOR_SHEET_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.SOLID_COLOR_SHEET_SETTING)
            color = color_utils.descriptor2hex(setting[Klass.Color])
            svg_utils.set_attribute(node, "fill", color)
        elif Tag.PATTERN_FILL_SETTING in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(Tag.PATTERN_FILL_SETTING)
            logger.warning(f"Pattern fill is not supported yet: {setting}")
        elif Tag.GRADIENT_FILL_SETTING in layer.tagged_blocks:
            # classID is null for gradient fill setting.
            setting = layer.tagged_blocks.get_data(Tag.GRADIENT_FILL_SETTING)
            gradient = self.add_gradient_definition(setting)
            if gradient is not None:
                svg_utils.set_attribute(node, "fill", svg_utils.get_funciri(gradient))
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
                logger.warning(f"No color stop found at location: {location}")
                stop_color = None
                # TODO: Get interpolated color
            else:
                stop_color = color_utils.descriptor2hex(color_stops[location])
            if location not in opacity_stops:
                logger.warning(f"No opacity stop found at location: {location}")
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
            logger.warning("Gradient midpoint is not supported.")

        return node

    def set_gradient_attributes(
        self, setting: Descriptor, gradient: ET.Element
    ) -> None:
        """Set gradient settings such as angle to the gradient element."""
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
        x2 = float(corners[b"rectangleCornerC"][b"Hrzn"])
        y2 = float(corners[b"rectangleCornerC"][b"Vrtc"])
        transform = origination._data[b"Trnf"]
        xx = float(transform[b"xx"])
        xy = float(transform[b"xy"])
        yx = float(transform[b"yx"])
        yy = float(transform[b"yy"])
        tx = float(transform[b"tx"])
        ty = float(transform[b"ty"])
        # Corners are in transformed space. Invert to get original coordinates.
        X = np.array([[x1, y1, 1], [x2, y2, 1]]).T
        M = np.array([[xx, yx, tx], [xy, yy, ty], [0, 0, 1]])
        # Apply inverse transform: Y = M^-1 @ X, then offset by reference point
        Y = np.linalg.solve(M, X) + np.array([[reference[0]], [reference[1]], [0]])
        bbox = (float(Y[0, 0]), float(Y[1, 0]), float(Y[0, 1]), float(Y[1, 1]))
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
