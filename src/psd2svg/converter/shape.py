# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
from psd_tools.constants import TaggedBlock, PathResource
from psd2svg.converter.constants import BLEND_MODE


logger = getLogger(__name__)


class ShapeConverter(object):

    STROKE_STYLE_LINE_CAP_TYPES = {
        b'strokeStyleButtCap': 'butt',
        b'strokeStyleRoundCap': 'round',
        b'strokeStyleSquareCap': 'square',
    }

    STROKE_STYLE_LINE_JOIN_TYPES = {
        b'strokeStyleMiterJoin': 'miter',
        b'strokeStyleRoundJoin': 'round',
        b'strokeStyleBevelJoin': 'bevel',
    }

    def generate_path(self, vector_mask, command='C'):
        """Sequence generator for SVG path constructor."""
        knots = vector_mask.knots
        if len(knots) == 0:
            return

        # Initial point.
        yield 'M'
        yield knots[0]['anchor'][1] * self.width
        yield knots[0]['anchor'][0] * self.height
        yield command

        # Closed path or open path
        closed = vector_mask.closed
        points = (zip(knots, knots[1:] + knots[0:1])
                  if closed else zip(knots, knots[1:]))

        # Rest of the points.
        for p1, p2 in points:
            yield p1['control_leaving_knot'][1] * self.width
            yield p1['control_leaving_knot'][0] * self.height
            yield p2['control_preceding_knot'][1] * self.width
            yield p2['control_preceding_knot'][0] * self.height
            yield p2['anchor'][1] * self.width
            yield p2['anchor'][0] * self.height

        if closed:
            yield 'Z'


    def add_stroke_style(self, layer, element):
        """Add stroke style to the path element."""
        if not layer.has_stroke():
            return element

        stroke = layer.stroke
        if not stroke.stroke_enabled:
            return element

        if stroke.line_alignment == b'strokeStyleAlignInside':
            clippath = self._dwg.defs.add(self._dwg.clipPath())
            clippath['class'] = 'psd-stroke stroke-inside'
            clippath.add(self._dwg.path(
                self.generate_path(layer.vector_mask)))
            element['stroke-width'] = stroke.line_width * 2
            element['clip-path'] = clippath.get_funciri()
        elif stroke.line_alignment == b'strokeStyleAlignOutside':
            mask = self._dwg.defs.add(self._dwg.mask())
            mask['class'] = 'psd-stroke stroke-outside'
            mask.add(self._dwg.rect(
                insert=(layer.left, layer.top),
                size=(layer.width, layer.height),
                fill='white'))
            mask.add(self._dwg.path(
                self.generate_path(layer.vector_mask), fill='black'))
            element['stroke-width'] = stroke.line_width * 2
            element['mask'] = mask.get_funciri()
        else:
            element['stroke-width'] = stroke.line_width

        if stroke.fill_enabled:
            if stroke.content.name == 'PatternOverlay':
                pattern = self.create_pattern(
                    stroke.content, insert=(layer.left, layer.top))
                element['stroke'] = pattern.get_funciri()
            elif stroke.content.name == 'GradientOverlay':
                bbox = layer.get_bbox()
                if bbox.is_empty():
                    bbox = layer.get_bbox(vector=True)
                gradient = self.create_gradient(
                    stroke.content, size=(bbox.width, bbox.height))
                element['stroke'] = gradient.get_funciri()
            elif stroke.content.name == 'ColorOverlay':
                element['stroke'] = self.create_solid_color(stroke.content)

        element['stroke-opacity'] = stroke.opacity / 100.0
        element['stroke-linecap'] = self.STROKE_STYLE_LINE_CAP_TYPES.get(
            stroke.line_cap_type)
        element['stroke-linejoin'] = self.STROKE_STYLE_LINE_JOIN_TYPES.get(
            stroke.line_join_type)
        if stroke.line_dash_set:
            element['stroke-dasharray'] = ",".join(
                [str(x * stroke.line_width) for x in stroke.line_dash_set])
            element['stroke-dashoffset'] = stroke.line_dash_offset
        self.add_blend_mode(element, stroke.blend_mode)

        return element


    def add_stroke_content_style(self, layer, element):
        """Add stroke content (fill) style to the path element."""
        if not layer.has_stroke_content():
            return element

        effect = layer.stroke_content
        if not effect.enabled:
            return element

        if effect.name == 'PatternOverlay':
            pattern = self.create_pattern(
                effect, insert=(layer.left, layer.top))
            element['fill'] = pattern.get_funciri()
        elif effect.name == 'GradientOverlay':
            bbox = layer.get_bbox()
            if bbox.is_empty():
                bbox = layer.get_bbox(vector=True)
            gradient = self.create_gradient(
                effect, size=(bbox.width, bbox.height))
            element['fill'] = gradient.get_funciri()
        if effect.name == 'ColorOverlay':
            element['fill'] = self.create_solid_color(effect)

        return element
