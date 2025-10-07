import logging
import math
import xml.etree.ElementTree as ET

from psd_tools.api import effects, layers
from psd_tools.terminology import Enum

from psd2svg.core import svg_utils, color_utils
from psd2svg.core.base import ConverterProtocol

logger = logging.getLogger(__name__)


class EffectConverter(ConverterProtocol):
    """Effect converter mixin."""

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

    def add_raster_color_overlay_effect(
        self, effect: effects.ColorOverlay, target: ET.Element
    ) -> ET.Element:
        """Add a color overlay filter to the SVG document.

        SVG does not allow coloring a raster image directly, so we create a filter.
        """
        filter = svg_utils.create_node(
            "filter", parent=self.current, id=self.auto_id("coloroverlay_")
        )
        svg_utils.create_node(
            "feFlood",
            parent=filter,
            flood_color=color_utils.descriptor2hex(effect.color),
            flood_opacity=effect.opacity / 100.0,
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
        use = svg_utils.create_node(
            "use",
            parent=self.current,
            href=svg_utils.get_uri(target),
            fill=color_utils.descriptor2hex(effect.color),
        )
        if effect.opacity != 100.0:
            svg_utils.set_attribute(use, "opacity", effect.opacity / 100.0)
        return use

    def apply_stroke_effect(self, layer: layers.Layer, target: ET.Element) -> None:
        """Apply stroke effects to the target element."""
        effect_list = list(layer.effects.find("stroke", enabled=True))
        for effect in reversed(effect_list):
            assert isinstance(effect, effects.Stroke)

            if isinstance(layer, layers.ShapeLayer):
                use = self.add_vector_stroke_effect(effect, target)
            else:
                use = self.add_raster_stroke_effect(effect, target)

            if effect.blend_mode != Enum.Normal:
                self.set_blend_mode(effect.blend_mode, use)

    def add_raster_stroke_effect(
        self, effect: effects.Stroke, target: ET.Element
    ) -> ET.Element:
        """Add a stroke filter to the SVG document.

        SVG does not allow stroking a raster image directly, so we create a filter.
        """
        logger.debug(f"Adding raster stroke effect: {effect}")
        filter = svg_utils.create_node(
            "filter", parent=self.current, id=self.auto_id("stroke_")
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
            flood_opacity=effect.opacity / 100.0,
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
            logger.warning("Pattern stroke is not supported yet.")
        elif effect.gradient is not None:
            logger.warning("Gradient stroke is not supported yet.")

        if effect.opacity != 100.0:
            svg_utils.set_attribute(use, "stroke-opacity", effect.opacity)
        if float(effect.size) != 1.0:
            svg_utils.set_attribute(use, "stroke-width", float(effect.size))

        # TODO: Check position, phase, and offset.
        if effect.position != Enum.CenteredFrame:
            position = Enum(effect.position)  # For validation.
            logger.warning(
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
            if insert_before_target:
                # Push the target element after the <use> element.
                self.current.remove(target)
                self.current.append(target)

    def add_raster_drop_shadow_effect(
        self, effect: effects.DropShadow, target: ET.Element
    ) -> ET.Element:
        """Add a drop shadow filter to the SVG document."""
        filter = svg_utils.create_node(
            "filter",
            parent=self.current,
            id=self.auto_id("dropshadow_"),
            x="-25%",
            y="-25%",
            width="150%",
            height="150%",
        )
        choke = float(effect.choke)
        size = float(effect.size)
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
            flood_opacity=effect.opacity / 100.0,
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


def polar_to_cartesian(angle: float, distance: float) -> tuple[float, float]:
    """Convert the polar coordinate to dx and dy."""
    angle_rad = angle * math.pi / 180.0
    return -distance * math.cos(angle_rad), distance * math.sin(angle_rad)
