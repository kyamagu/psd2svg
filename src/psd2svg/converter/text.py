# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
from psd2svg.converter.constants import JUSTIFICATIONS
from psd2svg.utils.color import cmyk2rgb
from psd2svg.utils.xml import safe_utf8


logger = getLogger(__name__)


class TextConverter(object):

    def _get_text(self, layer):
        text_info = _get_text_info(layer)
        if not text_info:
            return None

        text = self._dwg.text('', insert=(0, 0))
        text['font-size'] = 0  # To discard whitespace between spans.
        text['text-anchor'] = 'middle'

        transform = text_info['matrix']
        if transform[1] != 0.0 and transform[2] != 0.0:
            text['transform'] = 'matrix{}'.format(transform)
        elif transform[0] != 1.0 and transform[3] != 1.0:
            text['transform'] = 'translate({},{}) scale({},{})'.format(
                transform[4], transform[5], transform[0], transform[3])
        else:
            text['transform'] = 'translate({},{})'.format(
                transform[4], transform[5])

        text['text-anchor'] = JUSTIFICATIONS.get(
            text_info['justification'], 'start')

        if text_info['direction']:
            text['writing-mode'] = 'tb'
            text['glyph-orientation-vertical'] = 0

        newline = False
        for span in text_info['spans']:
            rspans = span[b'Text'].split('\r')
            for index in range(len(rspans)):
                if index > 0:
                    newline = True
                if len(rspans[index]) == 0:
                    continue

                value = safe_utf8(rspans[index]).replace(u' ', '\u00a0')
                # Whitespace workaround, because newline is ignored.
                tspan = self._dwg.tspan(value)
                if newline:
                    if text_info['direction']:
                        tspan['y'] = 0
                        tspan['dx'] = '-1em'
                    else:
                        tspan['x'] = 0
                        tspan['dy'] = '1em'
                    newline = False

                tspan['font-family'] = span[b'Font'][b'Name']

                if int(span[b'Font'][b'Synthetic']) & 1:
                    tspan['font-style'] = 'italic'
                if int(span[b'Font'][b'Synthetic']) & 2:
                    tspan['font-weight'] = 'bold'

                fontsize = span.get(b'FontSize', 12)  # Not sure default 12...
                # SVG cannot apply per-letter scaling...
                if span.get(b'HorizontalScale', None) is not None:
                    fontsize *= span[b'HorizontalScale']
                tspan['font-size'] = fontsize
                if span.get(b'Tracking', None):
                    tspan['letter-spacing'] = span[b'Tracking'] / 100

                decoration = []
                if span.get(b'Underline', False):
                    decoration.append('underline')
                if span.get(b'Strikethrough', False):
                    decoration.append('line-through')
                if len(decoration) > 0:
                    tspan['text-decoration'] = " ".join(decoration)

                if b'FillColor' in span:
                    if span[b'FillColor'][b'Type'] == 0:
                        gray = span[b'FillColor'][b'Values'][1]
                        rgb = (gray, gray, gray)
                    elif span[b'FillColor'][b'Type'] == 1:
                        rgb = [int(c*255) for c in
                               span[b'FillColor'][b'Values'][1:]]
                        if len(rgb) != 3:
                            raise ValueError('Unsupported FillColor')
                    elif span[b'FillColor'][b'Type'] == 2:
                        cmyk = span[b'FillColor'][b'Values'][1:]
                        if len(cmyk) != 4:
                            raise ValueError('Unsupported FillColor')
                        rgb = [int(round(c * 100)) for c in cmyk2rgb(cmyk)]
                    else:
                        raise ValueError('Unsupported FillColor')
                    opacity = span[b'FillColor'][b'Values'][0]
                else:
                    rgb = (0, 0, 0)
                    opacity = 1.0
                tspan['fill'] = 'rgb({},{},{})'.format(*rgb)
                tspan['fill-opacity'] = opacity

                text.add(tspan)

        return text


def _get_text_info(layer):
    type_info = dict(layer._record.tagged_blocks).get(b'TySh', None)
    if type_info is None:
        return None
    engine_data = dict(type_info.text_data.items)[b'EngineData']
    fontset = engine_data[b'DocumentResources'][b'FontSet']
    direction = engine_data[b'EngineDict'][
        b'Rendered'][b'Shapes'][b'WritingDirection']
    # Matrix [xx xy yx yy tx ty] applies affine transformation.
    matrix = (type_info.xx, type_info.xy, type_info.yx, type_info.yy,
              type_info.tx, type_info.ty)

    paragraphs = engine_data[b'EngineDict'][b'ParagraphRun'][b'RunArray']
    justification = paragraphs[0][
        b'ParagraphSheet'][b'Properties'].get(b'Justification', 0)

    runlength = engine_data[b'EngineDict'][b'StyleRun'][b'RunLengthArray']
    runarray = engine_data[b'EngineDict'][b'StyleRun'][b'RunArray']
    text = engine_data[b'EngineDict'][b'Editor'][b'Text']

    start = 0
    spans = []
    for run, size in zip(runarray, runlength):
        runtext = text[start:start+size]
        stylesheet = run[b'StyleSheet'][b'StyleSheetData'].copy()
        stylesheet[b'Text'] = runtext
        stylesheet[b'Font'] = fontset[stylesheet.get(b'Font', 0)]
        spans.append(stylesheet)
        start += size
    return {'direction': direction,
            'spans': spans,
            'justification': justification,
            'matrix': matrix}
