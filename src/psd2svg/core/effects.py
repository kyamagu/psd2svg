import logging
import math
import xml.etree.ElementTree as ET

from psd_tools.api import effects, layers
from psd_tools.constants import Tag
from psd_tools.psd.descriptor import UnitFloat
from psd_tools.terminology import Enum, Key, Klass, Unit

from psd2svg import svg_utils
from psd2svg.core import color_utils
from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class EffectConverter(ConverterProtocol):
    """Effect converter mixin."""

    def apply_background_effects(
        self, layer: layers.Layer, target: ET.Element, insert_before_target: bool = True
    ) -> None:
        """Apply background effects to the target element."""
        self.apply_drop_shadow_effect(
            layer, target, insert_before_target=insert_before_target
        )
        self.apply_outer_glow_effect(
            layer, target, insert_before_target=insert_before_target
        )

    def apply_overlay_effects(self, layer: layers.Layer, target: ET.Element) -> None:
        """Apply overlay effects to the target element."""
        self.apply_color_overlay_effect(layer, target)
        self.apply_gradient_overlay_effect(layer, target)
        self.apply_pattern_overlay_effect(layer, target)
        self.apply_inner_shadow_effect(layer, target)
        self.apply_inner_glow_effect(layer, target)
        self.apply_satin_effect(layer, target)
        self.apply_bevel_emboss_effect(layer, target)

    def apply_color_overlay_effect(
        self, layer: layers.Layer, target: ET.Element
    ) -> None:
        """Apply color overlay effect to the target element."""
        effect_list = list(layer.effects.find("coloroverlay", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.ColorOverlay)

            if isinstance(layer, layers.ShapeLayer):
                use = self.add_vector_color_overlay_effect(effect, target)
            else:
                use = self.add_raster_color_overlay_effect(effect, target)

            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)
            if effect.opacity != 100.0:
                self.set_opacity(effect.opacity / 100.0, use)

    def add_raster_color_overlay_effect(
        self, effect: effects.ColorOverlay, target: ET.Element
    ) -> ET.Element:
        """Add a color overlay filter to the SVG document.

        SVG does not allow coloring a raster image directly, so we create a filter.
        """
        filter = svg_utils.create_node(
            "filter", parent=self.current, id=self.auto_id("coloroverlay")
        )
        svg_utils.create_node(
            "feFlood",
            parent=filter,
            flood_color=color_utils.descriptor2hex(effect.color),
        )
        svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="in",
            in2="SourceAlpha",
        )
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            filter=svg_utils.get_funciri(filter),
        )
        return use

    def add_vector_color_overlay_effect(
        self, effect: effects.ColorOverlay, target: ET.Element
    ) -> ET.Element:
        """Add a color overlay effect to the current element using vector path."""
        return svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            fill=color_utils.descriptor2hex(effect.color),
        )

    def apply_stroke_effect(self, layer: layers.Layer, target: ET.Element) -> None:
        """Apply stroke effects to the target element."""
        effect_list = list(layer.effects.find("stroke", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.Stroke)

            if not isinstance(layer, layers.ShapeLayer) or "stroke" in target.attrib:
                # NOTE: If there is already a stroke, we need to stroke around the stroke.
                # This case happens when there is a stroke-only shape layer.
                use = self.add_raster_stroke_effect(layer, effect, target)
                if effect.opacity != 100.0:
                    self.set_opacity(effect.opacity / 100.0, use)
            else:
                use = self.add_vector_stroke_effect(layer, effect, target)
                # Vector stroke has stroke-opacity attribute. Skip setting opacity.

            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)

    def add_raster_stroke_effect(
        self, layer: layers.Layer, effect: effects.Stroke, target: ET.Element
    ) -> ET.Element:
        """Add a stroke filter to the SVG document.

        SVG does not allow stroking a raster image directly, so we create a filter.
        """
        filter = svg_utils.create_node(
            "filter", parent=self.current, id=self.auto_id("stroke")
        )

        # Create stroke area using morphology and composite.
        if effect.position == Enum.OutsetFrame:
            svg_utils.create_node(
                "feMorphology",
                parent=filter,
                operator="dilate",
                radius=float(effect.size),
                in_="SourceAlpha",
            )
            svg_utils.create_node(
                "feComposite",
                parent=filter,
                operator="xor",
                in2="SourceAlpha",
                result="STROKEAREA",
            )
        elif effect.position == Enum.InsetFrame:
            svg_utils.create_node(
                "feMorphology",
                parent=filter,
                operator="erode",
                radius=float(effect.size),
                in_="SourceAlpha",
            )
            svg_utils.create_node(
                "feComposite",
                parent=filter,
                operator="xor",
                in2="SourceAlpha",
                result="STROKEAREA",
            )
        elif effect.position == Enum.CenteredFrame:
            svg_utils.create_node(
                "feMorphology",
                parent=filter,
                operator="dilate",
                radius=float(effect.size) / 2.0,
                in_="SourceAlpha",
                result="DILATED",
            )
            svg_utils.create_node(
                "feMorphology",
                parent=filter,
                operator="erode",
                radius=float(effect.size) / 2.0,
                in_="SourceAlpha",
                result="ERODED",
            )
            svg_utils.create_node(
                "feComposite",
                parent=filter,
                operator="xor",
                in_="DILATED",
                in2="ERODED",
                result="STROKEAREA",
            )
        else:
            raise ValueError(f"Unsupported stroke position: {effect.position}")

        # Gradient and pattern strokes needs feImage.
        if effect.fill_type == Enum.SolidColor:
            svg_utils.create_node(
                "feFlood",
                parent=filter,
                flood_color=color_utils.descriptor2hex(effect.color),
            )
        elif effect.fill_type == Enum.Pattern:
            if effect.pattern is None:
                raise ValueError("Stroke pattern is None for pattern fill type.")
            pattern = self.add_pattern(layer._psd, effect.pattern)
            self.set_pattern_effect_transform(pattern, effect, (0, 0))
            defs = svg_utils.create_node("defs", parent=self.current)
            rect = svg_utils.create_node(
                "rect",
                parent=defs,
                id=self.auto_id("patternstroke"),
                width="100%",
                height="100%",
                fill=svg_utils.get_funciri(pattern),
            )
            svg_utils.create_node(
                "feImage",
                parent=filter,
                href=svg_utils.get_uri(rect),
            )
        elif effect.fill_type == Enum.GradientFill:
            if effect.gradient is None:
                raise ValueError("Stroke gradient is None for gradient fill type.")
            gradient = None
            if effect.type == Enum.Linear:
                gradient = self.add_linear_gradient(effect.gradient)
            elif effect.type == Enum.Radial:
                gradient = self.add_radial_gradient(effect.gradient)
            else:
                logger.warning(
                    f"Only linear and radial gradient strokes are supported: {effect}"
                )
                # Fallback to simple color.
                flood_color = (
                    color_utils.descriptor2hex(effect.color)
                    if effect.color
                    else "#ffffff"
                )
                svg_utils.create_node("feFlood", parent=filter, flood_color=flood_color)
            if gradient is not None:
                self.set_gradient_transform(layer, gradient, effect)
                defs = svg_utils.create_node("defs", parent=self.current)
                rect = svg_utils.create_node(
                    "rect",
                    parent=defs,
                    id=self.auto_id("gradientstroke"),
                    width="100%",
                    height="100%",
                    fill=svg_utils.get_funciri(gradient),
                )
                svg_utils.create_node(
                    "feImage",
                    parent=filter,
                    href=svg_utils.get_uri(rect),
                )
        svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="in",
            in2="STROKEAREA",
        )
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            filter=svg_utils.get_funciri(filter),
        )
        return use

    def add_vector_stroke_effect(
        self, layer: layers.Layer, effect: effects.Stroke, target: ET.Element
    ) -> ET.Element:
        """Add a stroke effect to the current element using vector path."""

        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            fill="transparent",
        )
        # Check effect.fill_type.
        if effect.fill_type == Enum.SolidColor:
            if effect.color is None:
                raise ValueError("Stroke color is None for color fill type.")
            color = color_utils.descriptor2hex(effect.color)
            svg_utils.set_attribute(use, "stroke", color)
        elif effect.fill_type == Enum.Pattern:
            if effect.pattern is None:
                raise ValueError("Stroke pattern is None for pattern fill type.")
            pattern = self.add_pattern(layer._psd, effect.pattern)
            self.set_pattern_effect_transform(pattern, effect, (0, 0))
            svg_utils.set_attribute(use, "stroke", svg_utils.get_funciri(pattern))
        elif effect.fill_type == Enum.GradientFill:
            if effect.gradient is None:
                raise ValueError("Stroke gradient is None for gradient fill type.")
            if effect.type == Enum.Linear:
                gradient = self.add_linear_gradient(effect.gradient)
            elif effect.type == Enum.Radial:
                gradient = self.add_radial_gradient(effect.gradient)
            else:
                logger.warning(
                    f"Only linear and radial gradient strokes are supported: {effect}"
                )
                return use
            self.set_gradient_transform(layer, gradient, effect)
            svg_utils.set_attribute(use, "stroke", svg_utils.get_funciri(gradient))

        if effect.opacity != 100.0:
            svg_utils.set_attribute(use, "stroke-opacity", effect.opacity)
        if float(effect.size) != 1.0:
            svg_utils.set_attribute(use, "stroke-width", float(effect.size))

        # TODO: Check position, phase, and offset.
        if effect.position != Enum.CenteredFrame:
            position = Enum(effect.position)  # For validation.
            logger.info(
                f"Only centered stroke position is supported in SVG: {position.name}"
            )

        return use

    def apply_drop_shadow_effect(
        self,
        layer: layers.Layer,
        target: ET.Element,
        insert_before_target: bool = False,
    ) -> None:
        """Apply drop shadow effect to the current element."""
        effect_list = list(layer.effects.find("dropshadow", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.DropShadow)
            use = self.add_raster_drop_shadow_effect(effect, target)
            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)
            if effect.opacity != 100.0:
                self.set_opacity(effect.opacity / 100.0, use)
            if insert_before_target:
                # Push the target element after the <use> element.
                self.current.remove(target)
                self.current.append(target)

    def add_raster_drop_shadow_effect(
        self, effect: effects.DropShadow, target: ET.Element
    ) -> ET.Element:
        """Add a drop shadow filter to the SVG document."""
        choke = float(effect.choke)
        size = float(effect.size)
        # TODO: Adjust the width and height based on size.
        filter = svg_utils.create_node(
            "filter",
            parent=self.current,
            id=self.auto_id("dropshadow"),
            x="-25%",
            y="-25%",
            width="150%",
            height="150%",
        )
        svg_utils.create_node(
            "feMorphology",
            parent=filter,
            operator="dilate",
            radius=choke / 100.0 * size,
            in_="SourceAlpha",
        )
        svg_utils.create_node(
            "feGaussianBlur",
            parent=filter,
            stdDeviation=(100.0 - choke) / 100.0 * size / 2.0,
        )
        dx, dy = polar_to_cartesian(float(effect.angle), float(effect.distance))
        svg_utils.create_node(
            "feOffset",
            parent=filter,
            dx=dx,
            dy=dy,
            result="SHADOW",
        )
        svg_utils.create_node(
            "feFlood",
            parent=filter,
            flood_color=color_utils.descriptor2hex(effect.color),
        )
        svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="in",
            in2="SHADOW",
        )
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            filter=svg_utils.get_funciri(filter),
        )
        return use

    def apply_outer_glow_effect(
        self,
        layer: layers.Layer,
        target: ET.Element,
        insert_before_target: bool = False,
    ) -> None:
        """Apply outer glow effect to the current element."""
        effect_list = list(layer.effects.find("outerglow", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.OuterGlow)
            use = self.add_raster_outer_glow_effect(effect, target)
            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)
            if effect.opacity != 100.0:
                self.set_opacity(effect.opacity / 100.0, use)
            if insert_before_target:
                # Push the target element after the <use> element.
                self.current.remove(target)
                self.current.append(target)

    def add_raster_outer_glow_effect(
        self, effect: effects.OuterGlow, target: ET.Element
    ) -> ET.Element:
        """Add an outer glow filter to the SVG document."""
        choke = float(effect.choke)
        size = float(effect.size)
        # TODO: Adjust the width and height based on size.
        filter = svg_utils.create_node(
            "filter",
            parent=self.current,
            id=self.auto_id("outerglow"),
        )
        # TODO: Adjust radius and stdDeviation, as the rendering quality differs.
        svg_utils.create_node(
            "feMorphology",
            parent=filter,
            operator="dilate",
            radius=choke / 100.0 * size + (100.0 - choke) / 100.0 * size / 6.0,
            in_="SourceAlpha",
        )
        svg_utils.create_node(
            "feGaussianBlur",
            parent=filter,
            stdDeviation=(100.0 - choke) / 100.0 * size / 4.0,
            result="GLOW",
        )
        svg_utils.create_node(
            "feFlood",
            parent=filter,
            flood_color=color_utils.descriptor2hex(effect.color),
        )
        svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="in",
            in2="GLOW",
        )
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            filter=svg_utils.get_funciri(filter),
        )
        return use

    def apply_gradient_overlay_effect(
        self, layer: layers.Layer, target: ET.Element
    ) -> None:
        effect_list = list(layer.effects.find("gradientoverlay", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.GradientOverlay)
            if effect.type == Enum.Linear:
                gradient = self.add_linear_gradient(effect.gradient)
            elif effect.type == Enum.Radial:
                gradient = self.add_radial_gradient(effect.gradient)
            else:
                logger.warning(
                    "Only linear and radial gradient overlay are supported: "
                    f"{effect.type}: '{layer.name}' ({layer.kind})"
                )
                continue
            self.set_gradient_transform(layer, gradient, effect)

            if isinstance(layer, layers.ShapeLayer):
                use = self.add_vector_gradient_overlay_effect(gradient, target)
            else:
                use = self.add_raster_gradient_overlay_effect(gradient, target)

            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)
            if effect.opacity != 100.0:
                self.set_opacity(effect.opacity / 100.0, use)

    def add_raster_gradient_overlay_effect(
        self, gradient: ET.Element, target: ET.Element
    ) -> ET.Element:
        # feFlood does not support fill with gradient, so we use feImage and feComposite.
        defs = svg_utils.create_node("defs", parent=self.current)
        # Rect here should have the target size.
        rect = svg_utils.create_node(
            "rect",
            parent=defs,
            id=self.auto_id("gradientfill"),
            width=target.get("width", "100%"),
            height=target.get("height", "100%"),
            fill=svg_utils.get_funciri(gradient),
        )
        # Filter origin should be set to (0, 0) instead of (-10%, -10%).
        filter = svg_utils.create_node(
            "filter",
            parent=self.current,
            id=self.auto_id("gradientoverlay"),
            x="0",
            y="0",
        )
        svg_utils.create_node(
            "feImage",
            parent=filter,
            href=svg_utils.get_uri(rect),
        )
        svg_utils.create_node(
            "feComposite",
            in2="SourceAlpha",
            operator="in",
            parent=filter,
        )
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            filter=svg_utils.get_funciri(filter),
        )
        return use

    def add_vector_gradient_overlay_effect(
        self, gradient: ET.Element, target: ET.Element
    ) -> ET.Element:
        return svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            fill=svg_utils.get_funciri(gradient),
        )

    def set_gradient_transform(
        self,
        layer: layers.Layer,
        gradient: ET.Element,
        effect: effects.GradientOverlay | effects.Stroke,
    ) -> None:
        """Set gradient transformations based on the effect properties."""
        transforms = []
        aligned = effect.value.get(Key.Aligned) is True
        if aligned:
            # Gradient aligned to layer bounds.
            landscape = layer.width >= layer.height
            # Adjust the object coordinates.
            if layer.width != layer.height:
                if landscape:
                    transforms.append(
                        f"scale({svg_utils.num2str(layer.height / layer.width, digit=4)} 1)"
                    )
                else:
                    transforms.append(
                        f"scale(1 {svg_utils.num2str(layer.width / layer.height, digit=4)})"
                    )
            reference = (0.5, 0.5)
        else:
            # Gradient defined in user space (canvas).
            svg_utils.set_attribute(gradient, "gradientUnits", "userSpaceOnUse")
            landscape = self.psd.width >= self.psd.height
            reference = (self.psd.width / 2, self.psd.height / 2)

        # Set the base gradient direction based on the shorter edge.
        if landscape:
            # Vertical gradient.
            svg_utils.set_attribute(gradient, "x2", "0%")
            svg_utils.set_attribute(gradient, "y2", "100%")
        else:
            # Horizontal gradient.
            svg_utils.set_attribute(gradient, "x2", "100%")
            svg_utils.set_attribute(gradient, "y2", "0%")

        # Apply phase offset.
        if effect.offset is not None:
            # offset is b'Pnt ' descriptor with percentage values
            offset = (
                effect.offset[Key.Horizontal].value / 100.0,
                effect.offset[Key.Vertical].value / 100.0,
            )
            if not aligned:
                offset = (offset[0] * self.psd.width, offset[1] * self.psd.height)
            svg_utils.append_attribute(
                gradient,
                "gradientTransform",
                "translate(%s)" % svg_utils.seq2str(offset),
            )

        # Apply angle, scale, and offset transforms.
        angle = -float(effect.angle or 0)
        if landscape:
            angle -= 90
        if effect.reversed:
            angle += 180
        if angle != 0:
            transforms.append(f"rotate({svg_utils.num2str(angle)})")

        scale = float(effect.value.get(Key.Scale, UnitFloat(Unit.Percent, 100.0)).value)
        if scale != 100:
            if landscape:
                transforms.append(
                    f"scale(1 {svg_utils.num2str(scale / 100.0, digit=4)})"
                )
            else:
                transforms.append(
                    f"scale({svg_utils.num2str(scale / 100.0, digit=4)} 1)"
                )

        if transforms:
            # Move to the reference point, apply transforms, then move back.
            if reference != (0.0, 0.0):
                svg_utils.append_attribute(
                    gradient,
                    "gradientTransform",
                    "translate(%s)" % svg_utils.seq2str(reference, digit=4),
                )
            svg_utils.append_attribute(
                gradient, "gradientTransform", " ".join(transforms)
            )
            if reference != (0.0, 0.0):
                svg_utils.append_attribute(
                    gradient,
                    "gradientTransform",
                    "translate(%s)"
                    % svg_utils.seq2str((-reference[0], -reference[1]), digit=4),
                )

        if b"gs99" in effect.value:
            method = effect.value[b"gs99"]
            if method.enum == Enum.Perceptual:
                logger.info("Perceptual gradient interpolation is not accurate.")
            elif method.enum == Enum.Linear:
                logger.info("Linear gradient interpolation is not accurate.")
            elif method.enum == b"GIMs":  # Stripes
                logger.warning("Stripes gradient interpolation is not supported yet.")
            elif method.enum == b"Gcls":  # Classic
                pass  # Default is classic
            elif method.enum == Key.Smooth:  # Smooth
                logger.info("Smooth gradient interpolation is not accurate.")

    def apply_pattern_overlay_effect(
        self, layer: layers.Layer, target: ET.Element
    ) -> None:
        effect_list = list(layer.effects.find("patternoverlay", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.PatternOverlay)
            pattern = self.add_pattern(layer._psd, effect.pattern)
            reference = layer.tagged_blocks.get_data(Tag.REFERENCE_POINT, (0, 0))
            self.set_pattern_effect_transform(pattern, effect, reference)

            if isinstance(layer, layers.ShapeLayer):
                use = self.add_vector_pattern_overlay_effect(pattern, target)
            else:
                use = self.add_raster_pattern_overlay_effect(pattern, target)

            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)
            if effect.opacity != 100.0:
                self.set_opacity(effect.opacity / 100.0, use)

    def add_raster_pattern_overlay_effect(
        self, pattern: ET.Element, target: ET.Element
    ) -> ET.Element:
        # feFlood does not support fill with pattern, so we use feImage and feComposite.
        defs = svg_utils.create_node("defs", parent=self.current)

        if "x" not in target.attrib or "y" not in target.attrib:
            logger.debug(
                "Target element for raster pattern overlay effect "
                "does not have 'x' or 'y' attribute. "
                "Assuming (0, 0) as the origin."
            )
        # Rect here should have the target size and location.
        rect = svg_utils.create_node(
            "rect",
            parent=defs,
            id=self.auto_id("patternfill"),
            x=target.get("x", "0"),
            y=target.get("y", "0"),
            width=target.get("width", "100%"),
            height=target.get("height", "100%"),
            fill=svg_utils.get_funciri(pattern),
        )
        # Filter should use the user space coordinates here.
        filter = svg_utils.create_node(
            "filter",
            parent=self.current,
            id=self.auto_id("patternoverlay"),
            x=0,
            y=0,
            filterUnits="userSpaceOnUse",
        )
        svg_utils.create_node(
            "feImage",
            parent=filter,
            href=svg_utils.get_uri(rect),
        )
        svg_utils.create_node(
            "feComposite",
            in2="SourceAlpha",
            operator="in",
            parent=filter,
        )
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            filter=svg_utils.get_funciri(filter),
        )
        return use

    def add_vector_pattern_overlay_effect(
        self, pattern: ET.Element, target: ET.Element
    ) -> ET.Element:
        return svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            fill=svg_utils.get_funciri(pattern),
        )

    def set_pattern_effect_transform(
        self,
        pattern: ET.Element,
        effect: effects.PatternOverlay | effects.Stroke,
        reference: tuple[float, float],
    ) -> None:
        """Set pattern transformations based on the effect properties."""
        if reference != (0, 0):
            svg_utils.append_attribute(
                pattern,
                "patternTransform",
                f"translate({svg_utils.seq2str(reference)})",
            )
        if effect.phase is not None:
            assert effect.phase.classID == Klass.Point
            offset = (
                float(effect.phase[Key.Horizontal].value),
                float(effect.phase[Key.Vertical].value),
            )
            if offset[0] != 0.0 or offset[1] != 0.0:
                svg_utils.append_attribute(
                    pattern,
                    "patternTransform",
                    f"translate({svg_utils.seq2str(offset)})",
                )
        scale = float(effect.value.get(Key.Scale, UnitFloat(Unit.Percent, 100.0)).value)
        if scale != 100.0:
            svg_utils.append_attribute(
                pattern,
                "patternTransform",
                f"scale({svg_utils.num2str(scale / 100.0)})",
            )
        if effect.angle != 0.0:
            rotation = -effect.angle
            svg_utils.append_attribute(
                pattern,
                "patternTransform",
                f"rotate({svg_utils.num2str(rotation)})",
            )

    def apply_inner_shadow_effect(
        self, layer: layers.Layer, target: ET.Element
    ) -> None:
        effect_list = list(layer.effects.find("innershadow", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.InnerShadow)
            use = self.add_raster_inner_shadow_effect(effect, target)
            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)
            if effect.opacity != 100.0:
                self.set_opacity(effect.opacity / 100.0, use)

    def add_raster_inner_shadow_effect(
        self, effect: effects.InnerShadow, target: ET.Element
    ) -> ET.Element:
        """Add an inner shadow filter to the SVG document."""
        logger.debug(f"Adding raster inner shadow effect: {effect}")
        choke = float(effect.choke)
        size = float(effect.size)
        filter = svg_utils.create_node(
            "filter",
            parent=self.current,
            id=self.auto_id("innershadow"),
        )
        svg_utils.create_node(
            "feMorphology",
            parent=filter,
            operator="erode",
            radius=choke / 100.0 * size,
            in_="SourceAlpha",
        )
        svg_utils.create_node(
            "feGaussianBlur",
            parent=filter,
            stdDeviation=(100.0 - choke) / 100.0 * size / 2.0,
        )
        dx, dy = polar_to_cartesian(float(effect.angle), float(effect.distance))
        svg_utils.create_node(
            "feOffset",
            parent=filter,
            dx=dx,
            dy=dy,
            result="SHADOW",
        )
        svg_utils.create_node(
            "feFlood",
            parent=filter,
            flood_color=color_utils.descriptor2hex(effect.color),
        )
        svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="out",
            in2="SHADOW",
        )
        # Restrict the shadow to the inside of the original shape.
        svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="in",
            in2="SourceAlpha",
        )
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            filter=svg_utils.get_funciri(filter),
        )
        return use

    def apply_inner_glow_effect(self, layer: layers.Layer, target: ET.Element) -> None:
        effect_list = list(layer.effects.find("innerglow", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.InnerGlow)
            use = self.add_raster_inner_glow_effect(effect, target)
            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)
            if effect.opacity != 100.0:
                self.set_opacity(effect.opacity / 100.0, use)

    def add_raster_inner_glow_effect(
        self, effect: effects.InnerGlow, target: ET.Element
    ) -> ET.Element:
        """Add an inner glow filter to the SVG document."""
        # TODO: Support different glow types.
        if effect.glow_type != Enum.SoftMatte:
            logger.warning(f"Only softer inner glow is supported: {effect.glow_type}")
        choke = float(effect.choke)
        size = float(effect.size)
        # TODO: Adjust the width and height based on size.
        filter = svg_utils.create_node(
            "filter",
            parent=self.current,
            id=self.auto_id("innerglow"),
        )
        # TODO: Adjust radius and stdDeviation, as the rendering quality differs.
        svg_utils.create_node(
            "feMorphology",
            parent=filter,
            operator="erode",
            radius=choke / 100.0 * size + (100.0 - choke) / 100.0 * size / 6.0,
            in_="SourceAlpha",
        )
        svg_utils.create_node(
            "feGaussianBlur",
            parent=filter,
            stdDeviation=(100.0 - choke) / 100.0 * size / 4.0,
            result="GLOW",
        )
        svg_utils.create_node(
            "feFlood",
            parent=filter,
            flood_color=color_utils.descriptor2hex(effect.color),
        )
        svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="out" if effect.glow_source == Enum.EdgeGlow else "in",
            in2="GLOW",
        )
        svg_utils.create_node(
            "feComposite",
            parent=filter,
            operator="in",
            in2="SourceAlpha",
        )
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            filter=svg_utils.get_funciri(filter),
        )
        return use

    def apply_satin_effect(self, layer: layers.Layer, target: ET.Element) -> None:
        effect_list = list(layer.effects.find("satin", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.Satin)
            logger.warning(
                f"Satin effect is not supported yet: '{layer.name}' ({layer.kind})"
            )

    def apply_bevel_emboss_effect(
        self, layer: layers.Layer, target: ET.Element
    ) -> None:
        effect_list = list(layer.effects.find("bevelemboss", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.BevelEmboss)
            logger.warning(
                f"Bevel emboss effect is not supported yet: '{layer.name}' ({layer.kind})"
            )


def polar_to_cartesian(angle: float, distance: float) -> tuple[float, float]:
    """Convert the polar coordinate to dx and dy."""
    angle_rad = angle * math.pi / 180.0
    return -distance * math.cos(angle_rad), distance * math.sin(angle_rad)
