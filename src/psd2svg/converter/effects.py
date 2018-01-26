# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
import numpy as np
import svgwrite
from psd_tools.constants import TaggedBlock
from psd_tools.decoder.actions import List, Descriptor
from psd2svg.converter.constants import BLEND_MODE
from psd2svg.utils.color import cmyk2rgb


logger = getLogger(__name__)


class EffectsConverter(object):

    def _get_effects(self, layer):
        blocks = layer._tagged_blocks
        effects = blocks.get(
            b'lfx2', blocks.get(b'lfxs', blocks.get(b'lmfx', None)))
        enabled_effects = {}
        if effects:
            for key, info in effects.descriptor.items:
                if key == b'masterFXSwitch' and not info.value:
                    return None
                if isinstance(info, List):
                    info = info.items[0]
                if not isinstance(info, Descriptor):
                    continue
                items = dict(info.items)
                if not items[b'enab'].value:
                    continue
                enabled_effects[key] = items
            return None if len(enabled_effects) == 0 else enabled_effects
        else:
            return None

    def _add_effects(self, effects, layer, target, fill_opacity, blend_mode):
        effects_group = self._dwg.g()
        for index in reversed(range(len(target.elements))):
            if isinstance(target.elements[index], svgwrite.base.Title):
                effects_group.elements.append(target.elements.pop(index))
        effects_group['class'] = 'layer-effects'
        effects_group.get_iri()

        # TODO: b'ebbl' and multiple effects.

        # Outer effects.
        if b'DrSh' in effects:
            effects_group.add(self._add_drsh(
                effects[b'DrSh'], target.get_iri()))
        if b'OrGl' in effects:
            effects_group.add(self._add_orgl(
                effects[b'OrGl'], target.get_iri()))

        # TODO: clipped blending option clbl.
        self._add_interior_effects(effects, layer, effects_group, target,
                                   fill_opacity, blend_mode)

        # Stroke effect.
        if b'FrFX' in effects:
            effects_group.add(self._add_frfx(
                effects[b'FrFX'], target.get_iri()))

        return effects_group

    def _add_interior_effects(self, effects, layer, effects_group, target,
                              fill_opacity, blend_mode):
        # Fill effects turns source into mask. Otherwise render.
        mask_iri = None
        if (b'GrFl' in effects or b'SoFi' in effects or
                b'patternFill' in effects):
            self._dwg.defs.add(target)
            use = self._dwg.use(target.get_iri(), opacity=fill_opacity)
            if 'style' in target.attribs:
                use['style'] = target.attribs.pop('style')
            effects_group.add(use)
            mask_iri = self._make_fill_mask(layer, target.get_iri())
        elif fill_opacity < 1.0:
            self._dwg.defs.add(target)
            effects_group.add(self._dwg.use(
                target.get_iri(), opacity=fill_opacity))
        else:
            effects_group.add(target)

        if mask_iri:
            if b'patternFill' in effects:
                effects_group.add(self._add_patternfill(
                    effects[b'patternFill'], layer, mask_iri, blend_mode))
            if b'GrFl' in effects:
                effects_group.add(self._add_grfl(
                    effects[b'GrFl'], layer, mask_iri, blend_mode))
            if b'SoFi' in effects:
                effects_group.add(self._add_sofi(
                    effects[b'SoFi'], layer, mask_iri, blend_mode))

        # Inner effects.
        if b'IrSh' in effects:
            effects_group.add(self._add_irsh(
                effects[b'IrSh'], target.get_iri(), blend_mode))
        if b'IrGl' in effects:
            effects_group.add(self._add_irgl(
                effects[b'IrGl'], target.get_iri(), blend_mode))

    def _make_fill_mask(self, layer, target_iri):
        if not layer.bbox:
            logger.warning('Fill effect to empty layer.')
            return None

        mask = self._dwg.defs.add(self._dwg.mask(
            size=(layer.bbox.width, layer.bbox.height)
            ))
        mask['color-interpolation'] = 'sRGB'
        use = mask.add(self._dwg.use(target_iri))
        use['filter'] = self._get_white_filter().get_funciri()
        return mask.get_funciri()

    def _add_patternfill(self, items, layer, mask_iri, blend_mode):
        size = (layer.bbox.width, layer.bbox.height)
        pattern = self._make_pattern(items, (layer.bbox.x1, layer.bbox.y1))
        rect = self._dwg.rect(
            size=size,
            insert=(layer.bbox.x1, layer.bbox.y1),
            fill=pattern.get_funciri(), mask=mask_iri)
        rect['class'] = 'layer-effect pattern-fill'
        rect['fill-opacity'] = items[b'Opct'].value / 100.0

        if not blend_mode:
            blend_mode = BLEND_MODE.get(items[b'Md  '].value, 'normal')
        if blend_mode != 'normal':
            rect['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return rect

    def _add_grfl(self, items, layer, mask_iri, blend_mode):
        size = (layer.bbox.width, layer.bbox.height)
        grad = self._make_gradient(items, size)
        rect = self._dwg.rect(
            size=size,
            insert=(layer.bbox.x1, layer.bbox.y1),
            fill=grad.get_funciri(), mask=mask_iri)
        rect['class'] = 'layer-effect gradient-fill'
        opacity = items[b'Opct'].value / 100.0
        if opacity != 1.0:
            rect['fill-opacity'] = opacity

        if not blend_mode:
            blend_mode = BLEND_MODE.get(items[b'Md  '].value, 'normal')
        if blend_mode != 'normal':
            rect['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return rect

    def _add_sofi(self, items, layer, mask_iri, blend_mode):
        rect = self._dwg.rect(
            size=(layer.bbox.width, layer.bbox.height),
            insert=(layer.bbox.x1, layer.bbox.y1),
            fill=self._get_color_in_item(items), mask=mask_iri)
        rect['class'] = 'layer-effect solid-fill'
        rect['fill-opacity'] = items[b'Opct'].value / 100.0

        if not blend_mode:
            blend_mode = BLEND_MODE.get(items[b'Md  '].value, 'normal')
        if blend_mode != 'normal':
            rect['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return rect

    def _add_drsh(self, items, target_iri):
        blur = items[b'blur'].value
        blend_mode = BLEND_MODE.get(items[b'Md  '].value, 'normal')

        spread = items[b'Ckmt'].value / 100
        angle = items[b'lagl'].value
        radius = items[b'Dstn'].value
        dx = radius * np.cos(np.radians(angle))
        dy = radius * np.sin(np.radians(angle))

        filt = self._dwg.defs.add(self._dwg.filter(
            x='-50%', y='-50%', size=('200%', '200%')))
        filt['class'] = 'drop-shadow'
        filt.feOffset('SourceAlpha', dx=dx, dy=dy, result='drshOffset')
        filt.feGaussianBlur('drshOffset', stdDeviation=blur / 2,
                            result='drshBlur')
        transfer = filt.feComponentTransfer('drshBlur', result='drshBlurA')
        transfer.feFuncA('linear', slope=1.0 + 4 * spread, intercept=0.0)
        flood = filt.feFlood(result='drshFlood')
        flood['flood-color'] = self._get_color_in_item(items)
        flood['flood-opacity'] = items[b'Opct'].value / 100.0
        filt.feComposite('drshFlood', in2='drshBlurA', operator='in',
                         result='drshShadow')

        target = self._dwg.use(target_iri, filter=filt.get_funciri())
        target['class'] = 'layer-effect drop-shadow'
        if blend_mode != 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return target

    def _add_orgl(self, items, target_iri):
        blur = items[b'blur'].value
        blend_mode = BLEND_MODE.get(items[b'Md  '].value, 'normal')
        spread = items[b'Ckmt'].value / 100

        # Real outer glow needs distance transform.
        filt = self._dwg.defs.add(self._dwg.filter(
            x='-50%', y='-50%', size=('200%', '200%')))
        filt['class'] = 'outer-glow'
        # Saturate alpha mask before glow if non-zero spread.
        if spread > 0:
            transfer = filt.feComponentTransfer('SourceAlpha',
                                                result='orglAlpha')
            transfer.feFuncA('linear', slope=255, intercept=0.0)
            result = 'orglDilate'
            filt.feMorphology('orglAlpha', radius=blur * spread,
                              operator='dilate', result=result)
        else:
            result = 'SourceAlpha'
        filt.feGaussianBlur(
            result, stdDeviation=blur * (1 - spread), result='orglBlur')
        transfer = filt.feComponentTransfer('orglBlur', result='orglBlurA')
        transfer.feFuncA('linear', slope=1 + 4 * spread, intercept=0.0)
        flood = filt.feFlood(result='orglFlood')
        # TODO: Gradient fill
        flood['flood-color'] = color = self._get_color_in_item(items)
        flood['flood-opacity'] = items[b'Opct'].value / 100.0
        filt.feComposite('orglFlood', in2='orglBlurA', operator='in',
                         result='orglShadow')
        filt.feComposite('orglShadow', in2='SourceAlpha', operator='out',
                         result='orglShadowA')

        target = self._dwg.use(target_iri, filter=filt.get_funciri())
        target['class'] = 'layer-effect outer-glow'
        if blend_mode != 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return target

    def _add_irsh(self, items, target_iri, blend_mode):
        blur = items[b'blur'].value
        angle = items[b'lagl'].value
        radius = items[b'Dstn'].value
        dx = radius * np.cos(np.radians(angle))
        dy = radius * np.sin(np.radians(angle))

        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'inner-shadow'
        flood = filt.feFlood(result='irshFlood')
        flood['flood-color'] = color = self._get_color_in_item(items)
        flood['flood-opacity'] = items[b'Opct'].value / 100.0
        filt.feComposite('irshFlood', in2='SourceAlpha', operator='out',
                         result='irshShadow')
        filt.feOffset('irshShadow', dx=dx, dy=dy, result='irshOffset')
        filt.feGaussianBlur('irshOffset', stdDeviation=blur / 2,
                            result='irshBlur')
        filt.feComposite('irshBlur', in2='SourceAlpha', operator='in',
                         result='irshShadow')

        target = self._dwg.use(target_iri, filter=filt.get_funciri())
        target['class'] = 'layer-effect inner-shadow'
        if not blend_mode:
            blend_mode = BLEND_MODE.get(items[b'Md  '].value, 'normal')
        if blend_mode != 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return target

    def _add_irgl(self, items, target_iri, blend_mode):
        blur = items[b'blur'].value
        spread = items[b'Ckmt'].value / 100

        # Real inner glow needs distance transform.
        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'inner-glow'
        flood = filt.feFlood(result='irglFlood')
        # TODO: Gradient fill
        flood['flood-color'] = color = self._get_color_in_item(items)
        flood['flood-opacity'] = items[b'Opct'].value / 100.0
        # Saturate alpha mask before glow.
        transfer = filt.feComponentTransfer('SourceAlpha', result='irglAlpha')
        transfer.feFuncA('linear', slope=255, intercept=0)
        filt.feComposite('irglFlood', in2='irglAlpha', operator='out',
                         result='irglShadow')
        filt.feMorphology('irglShadow', radius=blur * spread,
                          operator='dilate', result='irglDilate')
        filt.feGaussianBlur('irglDilate', stdDeviation=blur * (1 - spread),
                            result='irglBlur')
        filt.feComposite('irglBlur', in2='irglAlpha', operator='in',
                         result='irglShadow')

        target = self._dwg.use(target_iri, filter=filt.get_funciri())
        target['class'] = 'layer-effect inner-glow'
        if not blend_mode:
            blend_mode = BLEND_MODE.get(items[b'Md  '].value, 'normal')
        if blend_mode != 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return target

    def _add_frfx(self, items, target_iri):
        radius = int(items[b'Sz  '].value)
        style = items[b'Styl'].value

        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'stroke'

        flood = filt.feFlood(result='frfxFlood')
        # TODO: Gradient or pattern fill
        flood['flood-color'] = self._get_color_in_item(items)
        flood['flood-opacity'] = items[b'Opct'].value / 100.0
        if style == b'OutF':
            filt.feMorphology('SourceAlpha', result='frfxMorph',
                              operator='dilate', radius=radius)
            filt.feComposite('frfxFlood', in2='frfxMorph', operator='in',
                             result='frfxBoundary')
            filt.feComposite('frfxBoundary', in2='SourceAlpha',
                             operator='out')
        elif style == b'InsF':
            filt.feMorphology('SourceAlpha', result='frfxMorph',
                              operator='erode', radius=radius)
            filt.feComposite('frfxFlood', in2='frfxMorph', operator='out',
                             result='frfxBoundary')
            filt.feComposite('frfxBoundary', in2='SourceAlpha',
                             operator='in')
        else:
            filt.feMorphology('SourceAlpha', result='frfxDilate',
                              operator='dilate', radius=radius / 2.0)
            filt.feMorphology('SourceAlpha', result='frfxErode',
                              operator='erode', radius=radius / 2.0)
            filt.feComposite('frfxDilate', in2='frfxErode', operator='out',
                             result='frfxMorph')
            filt.feComposite('frfxFlood', in2='frfxMorph', operator='in')

        target = self._dwg.use(target_iri, filter=filt.get_funciri())
        target['class'] = 'layer-effect stroke'
        blend_mode = BLEND_MODE.get(items[b'Md  '].value, 'normal')
        if blend_mode != 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return target

    def _get_color_in_item(self, items, scale=1):
        # TODO: Color space support other than RGB.
        if b'Clr ' in items:
            color = items[b'Clr ']
            if color.classID == b'Grsc':
                luminosity = (100.0 - color.items[0][1].value) / 100.0
                return 'rgb({0},{0},{0})'.format(int(255 * luminosity))
            elif color.classID == b'RGBC':
                color_items = dict(color.items)
                # b'Nm  ', b'bookID', b'bookKey' fields can exist.
                return 'rgb({},{},{})'.format(
                    int(color_items[b'Rd  '].value),
                    int(color_items[b'Grn '].value),
                    int(color_items[b'Bl  '].value))
            elif color.classID == b'CMYC':
                color_items = dict(color.items)
                cmyk = (color_items[b'Cyn '].value,
                        color_items[b'Mgnt'].value,
                        color_items[b'Ylw '].value,
                        color_items[b'Blck'].value)
                rgb = cmyk2rgb(cmyk)
                return 'rgb({},{},{})'.format(*map(int, rgb))
            else:
                logger.error('Unsupported color: {}'.format(color.classID))
                raise NotImplementedError
        elif b'Grad' in items:
            logger.warning('Unsupported gradient fill')
            grad = dict(items[b'Grad'].items)
            if b'Clrs' in grad:
                colors = grad[b'Clrs'].items
                colors = [tuple(int(c[1].value / scale)
                                for c in dict(clr.items)[b'Clr '].items)
                          for clr in colors]
                return 'rgb({},{},{})'.format(*colors[0])
            else:
                return 'rgb(255,255,255)'  # TODO: Get grad reference.
        else:
            logger.error('Unknown color in items: {}'.format(items.keys()))
            raise NotImplementedError

    def _get_fill(self, layer):
        blocks = layer._tagged_blocks
        if b'PtFl' in blocks:  # TODO implement
            logger.warning('Unsupported pattern fill')
            return 'none'
        for key in TaggedBlock._FILL_KEYS:
            if key in blocks:
                items = dict(blocks[key].data.items)
                return self._get_color_in_item(items)
        return 'none'

    def _make_pattern(self, items, insert=(0, 0)):
        pattern_id = dict(items[b'Ptrn'].items)[b'Idnt'].value
        patt = self._psd.patterns.get(pattern_id, None)
        if not patt:
            logger.warning('Pattern data not found')
            return patt

        pattern = self._dwg.defs.add(svgwrite.pattern.Pattern())
        pattern['width'] = patt.width
        pattern['height'] = patt.height
        pattern['patternUnits'] = 'userSpaceOnUse'
        pattern['patternContentUnits'] = 'userSpaceOnUse'

        align = items[b'Algn'].value
        phase = dict(items[b'phase'].items)
        phase = (phase[b'Hrzn'].value, phase[b'Vrtc'].value)
        scale = items[b'Scl '].value
        pattern['patternTransform'] = 'translate({},{}) scale({})'.format(
            insert[0] + phase[0], insert[1] + phase[1], scale / 100.0)
        pattern.add(self._dwg.image(
            self._get_image_href(patt.as_PIL()), insert=(0, 0),
            size=(patt.width, patt.height)))
        return pattern

    def _make_gradient(self, items, size):
        if items[b'Type'].value == b'Rdl ':
            grad = self._dwg.defs.add(svgwrite.gradients.RadialGradient(
                center=None, r=.5))
        else:
            theta = np.radians(-items[b'Angl'].value)
            start = np.array([size[0] * np.cos(theta - np.pi),
                              size[1] * np.sin(theta - np.pi)])
            end = np.array([size[0] * np.cos(theta), size[1] * np.sin(theta)])
            r = 1.0 * np.max(np.abs(start))
            start = start / (2 * r) + 0.5
            end = end / (2 * r) + 0.5

            start = [np.around(x, decimals=6) for x in start]
            end = [np.around(x, decimals=6) for x in end]

            grad = self._dwg.defs.add(svgwrite.gradients.LinearGradient(
                start=start, end=end))

        grad_items = dict(items[b'Grad'].items)
        if b'Clrs' not in grad_items:
            logger.warning('Unsupported gradient type')
            return grad
        color_list = [dict(v.items) for v in grad_items[b'Clrs'].items]
        opacity_list = [dict(v.items) for v in grad_items[b'Trns'].items]

        # Interpolate color and opacity for both points.
        cp = np.array([x[b'Lctn'].value / 4096 for x in color_list])
        op = np.array([x[b'Lctn'].value / 4096 for x in opacity_list])
        c_items = np.array([[y[1].value for y in x[b'Clr '].items] for x
                           in color_list]).transpose()
        o_items = np.array([x[b'Opct'].value / 100.0 for x in opacity_list])

        # Remove duplicate points.
        index = np.concatenate((np.diff(cp) > 0, [True]))
        if np.any(np.logical_not(index)):
            logger.warning('Duplicate gradient color stop: {}'.format(cp))
        cp = cp[index]
        c_items = c_items[:, index]
        index = np.concatenate((np.diff(op) > 0, [True]))
        if np.any(np.logical_not(index)):
            logger.warning('Duplicate gradient opacity stop: {}'.format(op))
        op = op[index]
        o_items = o_items[index]

        # Single point handling.
        if len(cp) < 2:
            cp = np.array([0.0, 1.0])
            c_items = np.concatenate((c_items, c_items), axis=1)
        if len(op) < 2:
            op = np.array([0.0, 1.0])
            o_items = np.array(list(o_items) + list(o_items))

        # Reverse if specified.
        if items[b'Rvrs'].value:
            cp = 1.0 - cp[::-1]
            op = 1.0 - op[::-1]
            c_items = c_items[:, ::-1]
            o_items = o_items[::-1]

        mp = np.unique(np.concatenate((cp, op)))
        fc = np.stack(
            [np.interp(mp, cp, c_items[index, :]) for index in range(3)])
        fo = np.interp(mp, op, o_items)

        for index in range(len(mp)):
            color = tuple(fc[:, index].astype(np.uint8).tolist())
            grad.add_stop_color(
                offset=mp[index], opacity=fo[index],
                color='rgb{}'.format(color))
        return grad

    def _get_white_filter(self, color='white'):
        if not self._white_filter:
            self._white_filter = self._dwg.defs.add(self._dwg.filter())
            self._white_filter['class'] = 'white-filter'
            if color == 'white':
                self._white_filter.feColorMatrix(
                    'SourceAlpha', type='matrix',
                    values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0")
            else:
                self._white_filter.feColorMatrix(
                    'SourceAlpha', type='matrix',
                    values="0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0")
        return self._white_filter

    def _get_identity_filter(self):
        if not self._identity_filter:
            self._identity_filter = self._dwg.defs.add(self._dwg.filter())
            self._identity_filter['class'] = 'identify-filter'
            transfer = self._identity_filter.feComponentTransfer(
                'SourceGraphic')
            transfer['color-interpolation'] = 'sRGB'
            transfer.feFuncR('identity')
            transfer.feFuncG('identity')
            transfer.feFuncB('identity')
            transfer.feFuncA('identity')
        return self._identity_filter
