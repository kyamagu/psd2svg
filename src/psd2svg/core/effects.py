import logging
import math
import xml.etree.ElementTree as ET

from psd_tools.api import effects, layers
from psd_tools.constants import Tag
from psd_tools.terminology import Enum, Key, Klass

from psd2svg.core import color_utils
from psd2svg.core.base import ConverterProtocol
from psd2svg import svg_utils

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

            if isinstance(layer, layers.ShapeLayer):
                use = self.add_vector_stroke_effect(effect, target)
                # Vector stroke has stroke-opacity attribute.
            else:
                use = self.add_raster_stroke_effect(effect, target)
                if effect.opacity != 100.0:
                    self.set_opacity(effect.opacity / 100.0, use)

            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)

    def add_raster_stroke_effect(
        self, effect: effects.Stroke, target: ET.Element
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

        # Fill type is always color for raster layers.
        svg_utils.create_node(
            "feFlood",
            parent=filter,
            flood_color=color_utils.descriptor2hex(effect.color),
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
        self, effect: effects.Stroke, target: ET.Element
    ) -> ET.Element:
        """Add a stroke effect to the current element using vector path."""

        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            fill="transparent",
        )
        # Check effect.fill_type.
        if effect.color is not None:
            color = color_utils.descriptor2hex(effect.color)
            svg_utils.set_attribute(use, "stroke", color)
        elif effect.pattern is not None:
            # TODO: Implement pattern stroke.
            logger.warning("Pattern stroke is not supported yet.")
        elif effect.gradient is not None:
            # TODO: Implement gradient stroke.
            logger.warning("Gradient stroke is not supported yet.")

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
            self.set_gradient_transform(gradient, effect)

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
        self, gradient: ET.Element, effect: effects.GradientOverlay
    ) -> None:
        """Set gradient transformations based on the effect properties."""
        if effect.reversed:
            svg_utils.append_attribute(
                gradient, "gradientTransform", "scale(-1 -1) translate(-1 -1)"
            )
        if effect.scale != 100.0:
            scale = effect.scale / 100.0
            svg_utils.append_attribute(
                gradient,
                "gradientTransform",
                f"translate(0.5 0.5) scale({scale:.0f} {scale:.0f}) translate(-0.5 -0.5)",
            )
        if effect.angle != 0.0:
            rotation = -effect.angle
            svg_utils.append_attribute(
                gradient,
                "gradientTransform",
                f"translate(0.5 0.5) rotate({rotation:.0f}) translate(-0.5 -0.5)",
            )

    def apply_pattern_overlay_effect(
        self, layer: layers.Layer, target: ET.Element
    ) -> None:
        effect_list = list(layer.effects.find("patternoverlay", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.PatternOverlay)
            pattern = self.add_pattern(layer._psd, effect.pattern)
            reference = layer.tagged_blocks.get_data(Tag.REFERENCE_POINT, (0, 0))
            self.set_pattern_transform(pattern, effect, reference)

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
            logger.warning(
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

    def set_pattern_transform(
        self,
        pattern: ET.Element,
        effect: effects.PatternOverlay,
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
        if effect.scale != 100.0:
            scale = effect.scale / 100.0
            svg_utils.append_attribute(
                pattern,
                "patternTransform",
                f"scale({svg_utils.num2str(scale, '.2f')})",
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
