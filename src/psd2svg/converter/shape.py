# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
from psd_tools.constants import TaggedBlock
from psd2svg.converter.constants import BLEND_MODE


logger = getLogger(__name__)


class ShapeConverter(object):

    def _get_vector_stroke(self, layer, target):
        blocks = layer._tagged_blocks
        if TaggedBlock.VECTOR_STROKE_DATA in blocks and (
                TaggedBlock.VECTOR_MASK_SETTING2 in blocks or
                TaggedBlock.VECTOR_MASK_SETTING1 in blocks):
            vstk = dict(blocks[TaggedBlock.VECTOR_STROKE_DATA].data.items)
            # vstk defines bezier curves.
            if vstk.get(b'strokeEnabled').value:
                vsms = blocks.get(
                    TaggedBlock.VECTOR_MASK_SETTING2,
                    blocks.get(TaggedBlock.VECTOR_MASK_SETTING1))
                return self._add_vstk(vstk, vsms, target.get_iri(),
                                      layer.bbox)
        return None

    def _generate_path(self, vsms, command='C'):
        # Iterator for SVG path constructor.
        anchors = [p for p in vsms.path if p['selector'] in (1, 2, 4, 5)]

        # Initial point.
        yield 'M'
        yield anchors[0]['anchor'][1] * self.width
        yield anchors[0]['anchor'][0] * self.height
        yield command

        # Closed path or open path
        closed = any(p['selector'] == 0 for p in vsms.path)
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

    def _add_vstk(self, vstk, vsms, target_iri, bbox):
        line_style = vstk[b'strokeStyleLineAlignment'].value
        target = self._dwg.path(self._generate_path(vsms, 'C'), fill='none')

        stroke_width = int(vstk[b'strokeStyleLineWidth'].value)
        if line_style == b'strokeStyleAlignInside':
            clippath = self._dwg.defs.add(self._dwg.clipPath())
            clippath['class'] = 'stroke-inside'
            clippath.add(self._dwg.path(self._generate_path(vsms)))
            target['stroke-width'] = stroke_width * 2
            target['clip-path'] = clippath.get_funciri()
        elif line_style == b'strokeStyleAlignOutside':
            mask = self._dwg.defs.add(self._dwg.mask())
            mask['class'] = 'stroke-outside'
            mask.add(self._dwg.rect(
                insert=(bbox.x1, bbox.y1), size=(bbox.width, bbox.height),
                fill='white'))
            mask.add(self._dwg.path(self._generate_path(vsms), fill='black'))
            target['stroke-width'] = stroke_width * 2
            target['mask'] = mask.get_funciri()
        else:
            target['stroke-width'] = stroke_width

        target['class'] = 'vector-stroke'

        style = dict(vstk[b'strokeStyleContent'].items)
        if vstk.get(b'strokeStyleContent').classID == b'solidColorLayer':
            target['stroke'] = self._get_color_in_item(style)
        elif vstk.get(b'strokeStyleContent').classID == b'patternLayer':
            pattern = self._make_pattern(style, insert=(bbox.x1, bbox.y1))
            target['stroke'] = pattern.get_funciri()
        else:
            grad = self._make_gradient(style, (bbox.width, bbox.height))
            target['stroke'] = grad.get_funciri()

        target['stroke-opacity'] = vstk[b'strokeStyleOpacity'].value / 100.0

        cap_type = vstk[b'strokeStyleLineCapType'].value
        if cap_type == b'strokeStyleButtCap':
            target['stroke-linecap'] = 'butt'
        elif cap_type == b'strokeStyleRoundCap':
            target['stroke-linecap'] = 'round'
        elif cap_type == b'strokeStyleSquareCap':
            target['stroke-linecap'] = 'square'

        join_type = vstk[b'strokeStyleLineJoinType'].value
        if join_type == b'strokeStyleMiterJoin':
            target['stroke-linejoin'] = 'miter'
        elif join_type == b'strokeStyleRoundJoin':
            target['stroke-linejoin'] = 'round'
        elif join_type == b'strokeStyleBevelJoin':
            target['stroke-linejoin'] = 'bevel'

        offset = int(vstk[b'strokeStyleLineDashOffset'].value)
        if offset:
            target['stroke-dashoffset'] = offset

        blend_mode = BLEND_MODE.get(
            vstk[b'strokeStyleBlendMode'].value, 'normal')
        if blend_mode != 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)

        return target
