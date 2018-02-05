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

    def _generate_path(self, vector_mask, command='C'):
        # Iterator for SVG path constructor.
        knot_types = (
            PathResource.CLOSED_SUBPATH_BEZIER_KNOT_LINKED,
            PathResource.CLOSED_SUBPATH_BEZIER_KNOT_UNLINKED,
            PathResource.OPEN_SUBPATH_BEZIER_KNOT_LINKED,
            PathResource.OPEN_SUBPATH_BEZIER_KNOT_UNLINKED
        )
        anchors = [p for p in vector_mask.path
                   if p['selector'] in knot_types]
        if len(anchors) == 0:
            return

        # Initial point.
        yield 'M'
        yield anchors[0]['anchor'][1] * self.width
        yield anchors[0]['anchor'][0] * self.height
        yield command

        # Closed path or open path
        closed = any(
            p['selector'] == PathResource.CLOSED_SUBPATH_LENGTH_RECORD
            for p in vector_mask.path
        )
        points = (zip(anchors, anchors[1:] + anchors[0:1])
                  if closed else zip(anchors, anchors[1:]))

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
                self._generate_path(layer.vector_mask)))
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
                self._generate_path(layer.vector_mask), fill='black'))
            element['stroke-width'] = stroke.line_width * 2
            element['mask'] = mask.get_funciri()
        else:
            element['stroke-width'] = stroke.line_width

        if stroke.fill_enabled:
            if stroke.content.name == 'ColorOverlay':
                element['stroke'] = self.create_solid_color(stroke.content)
            elif stroke.content.name == 'PatternOverlay':
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
