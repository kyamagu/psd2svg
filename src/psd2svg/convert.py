# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import io
from logging import getLogger
import psd_tools
import hashlib
import numpy as np
import psd_tools
import svgwrite
import re
import base64

from .storage import get_storage


logger = getLogger(__name__)


ILLEGAL_XML_RE = re.compile(
    '[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf'
    '\ufffe-\uffff]')


# https://helpx.adobe.com/photoshop/using/blending-modes.html
BLEND_MODE = {
    b'pass': 'normal /*pass*/',
    b'norm': 'normal',
    b'diss': 'normal /*dissolve*/',
    b'dark': 'darken',
    b'mul ': 'multiply',
    b'idiv': 'color-burn',
    b'lbrn': 'plus-darker /*linear-burn*/',  # Only webkit
    b'dkCl': 'darken /*darker-color*/',
    b'lite': 'lighten',
    b'scrn': 'screen',
    b'div ': 'color-dodge',
    b'lddg': 'plus-lighter /*linear-dodge*/',  # Only webkit
    b'lgCl': 'lighten /*lighter-color*/',
    b'over': 'overlay',
    b'sLit': 'soft-light',
    b'hLit': 'hard-light',
    b'vLit': 'lighten /*vivid-light*/',
    b'lLit': 'darken /*linear-light*/',
    b'pLit': 'normal /*pin-light*/',
    b'hMix': 'normal /*hard-mix*/',
    b'diff': 'difference',
    b'smud': 'exclusion',
    b'fsub': 'difference /*subtract*/',
    b'hue ': 'hue',
    b'sat ': 'saturation',
    b'colr': 'color',
    b'lum ': 'luminosity',
}

BLEND_MODE2 = {
    b'Nrml': 'normal',
    b'Dslv': 'normal /*dissolve*/',
    b'Drkn': 'darken',
    b'Mltp': 'multiply',
    b'CBrn': 'color-burn',
    b'linearBurn': 'plus-darker /*linear-burn*/',  # Only webkit
    b'darkerColor': 'darken',
    b'Lghn': 'lighten',
    b'Scrn': 'screen',
    b'CDdg': 'color-dodge',
    b'linearDodge': 'plus-lighter /*linear-dodge*/',  # Only webkit
    b'lighterColor': 'lighten /*lighter-color*/',
    b'Ovrl': 'overlay',
    b'SftL': 'soft-light',
    b'HrdL': 'hard-light',
    b'vividLight': 'lighten /*vivid-light*/',
    b'linearLight': 'darken /*linear-light*/',
    b'pinLight': 'normal /*pin-light*/',
    b'hardMix': 'normal /*hard-mix*/',
    b'Dfrn': 'difference',
    b'Xclu': 'exclusion',
    b'blendSubtraction': 'difference /*subtract*/',
    b'blendDivide': 'soft-light /*divide*/',
    b'H   ': 'hue',
    b'Strt': 'saturation',
    b'Clr ': 'color',
    b'Lmns': 'luminosity',
}

JUSTIFICATIONS = {
    0: 'start',
    1: 'end',
    2: 'middle',
}


class PSD2SVG(object):
    """PSD to SVG converter

    input_url - url or file-like object to input file
    output_url - url to export svg
    text_mode - option to switch text rendering (default 'image')
      * 'image' use Photoshop's bitmap
      * 'text' use SVG text
      * 'image-only' use Photoshop's bitmap and discard SVG text
      * 'text-only' use SVG text and discard Photoshop bitmap
    export_resource - use dataURI to embed bitmap (default True)
    """
    def __init__(self, text_mode='image', export_resource=False,
                 resource_prefix='', overwrite=True, reset_id=True):
        self.text_mode = text_mode
        self.export_resource = export_resource
        self.resource_prefix = resource_prefix
        self.overwrite = overwrite
        self.reset_id = reset_id
        self._psd = None

    @classmethod
    def run_convert(cls, input_url, output_url, **kwargs):
        converter = cls(**kwargs)
        converter.load(input_url)
        return converter.convert(output_url)

    def load(self, url):
        storage = get_storage(os.path.dirname(url))
        filename = os.path.basename(url)
        logger.info('Opening {}'.format(url))
        with storage.open(filename) as f:
            self.load_stream(f)
        self._input = url

    def load_stream(self, stream):
        self._input = None
        self._psd = psd_tools.PSDImage.from_stream(stream)

    def convert(self, output_url):
        self._set_output(output_url)

        if not self.overwrite and self._output.exists(self._output_file):
            url = self._output.url(self._output_file)
            logger.warning('File exists: {}'.format(url))
            return url

        if self.reset_id:
            svgwrite.utils.AutoID._set_value(0)
        self._white_filter = None
        self._identity_filter = None

        self._dwg = svgwrite.Drawing(
            size=(self.width, self.height),
            viewBox="0 0 {} {}".format(self.width, self.height))

        if self.text_mode in ('image', 'image-only'):
            stylesheet = 'text { display: none; }'
        elif self.text_mode in ('text', 'text-only'):
            stylesheet = '.text-image { display: none; }'
        self._dwg.defs.add(self._dwg.style(stylesheet))

        # Add layers.
        self._current_group = self._dwg
        self._add_group(self._psd.layers)

        # Embed photoshop view.
        image = self._psd.as_PIL()
        original = self._dwg.add(self._dwg.image(
            self._get_image_href(image), insert=(0, 0),
            size=(self.width, self.height), visibility='hidden'))
        original['class'] = 'photoshop-image'

        return self._save_svg()

    @property
    def width(self):
        return self._psd.header.width if self._psd else None

    @property
    def height(self):
        return self._psd.header.height if self._psd else None

    def _set_output(self, output_url):
        if not output_url.endswith('/') and os.path.isdir(output_url):
            output_url += '/'
        self._output = get_storage(os.path.dirname(output_url))
        self._resource = get_storage(
            self._output.url(self.resource_prefix))

        self._output_file = os.path.basename(output_url)
        if not self._output_file:
            if self._input:
                basename = os.path.splitext(os.path.basename(self._input))[0]
                self._output_file = basename + '.svg'
            else:
                raise ValueError('Invalid output: {}'.format(output_url))

    def _save_svg(self):
        # Write to the output.
        url = self._output.url(self._output_file)
        logger.info('Saving {}'.format(url))
        with io.StringIO() as f:
            self._dwg.write(f, pretty=True)
            self._output.put(self._output_file,
                             f.getvalue().encode('utf-8'))
        return url

    def _get_image_href(self, image, fmt='png', icc_profile=None):
        output = io.BytesIO()
        image.save(output, format=fmt, icc_profile=icc_profile)
        encoded_image = output.getvalue()
        output.close()
        checksum = hashlib.md5(encoded_image).hexdigest()
        if self.export_resource:
            filename = checksum + '.' + fmt
            if self.overwrite or not self._resource.exists(filename):
                logger.info('Saving {}'.format(
                    self._resource.url(filename)))
                self._resource.put(filename, encoded_image)
            href = os.path.join(self.resource_prefix, filename)
        else:
            href = ('data:image/{};base64,'.format(fmt) +
                    base64.b64encode(encoded_image).decode('utf-8'))
        return href

    def _add_group(self, layers):
        for layer in reversed(layers):
            self._add_layer(layer)

    def _add_layer(self, layer):
        target = self._get_target(layer)
        if target is None:
            return

        target.get_iri()  # Assign id
        mask = self._add_mask_if_exist(layer)
        effects = self._get_effects(layer)
        vector_stroke = self._get_vector_stroke(layer, target)

        logger.debug('{} {} {}'.format(layer.name, target, mask))

        if mask:
            target['mask'] = mask.get_funciri()

        # Blending options.
        if not layer._info.flags.visible:
            target['visibility'] = 'hidden'
        blend_mode = BLEND_MODE.get(layer._info.blend_mode, 'normal')
        if not blend_mode == 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        opacity, fill_opacity = self._get_opacity(layer)
        if opacity < 1.0:
            target['opacity'] = opacity

        if not effects and fill_opacity < 1.0:
            target['opacity'] = opacity * fill_opacity

        # TODO: Filter to strokes requires a different approach.
        blocks = layer._tagged_blocks

        if effects:
            interior_blend_mode = None
            if blocks.get(b'infx', False):
                interior_blend_mode = blend_mode
            target = self._add_effects(effects, layer, target, fill_opacity,
                                       interior_blend_mode)

        if layer._info.clipping and self._clip_group:
            self._clip_group.add(target)

            # Acutally clipping with mask and mix-blend-mode does not
            # correctly blend in SVG. clipPath does, but then cannot use
            # bitmap for clipping. Any workaround?
            self._clip_group['style'] = 'mix-blend-mode: {}'.format(
                blend_mode)
            if not self._clbl:
                self._clip_group.attribs['style'] += '; isolation: isolate;'

        elif layer._info.clipping:
            # Convert the last target to a clipping mask
            last_stroke = None
            last_target = self._current_group.elements[-1]
            if 'vector-stroke' in last_target.attribs.get(
                    'class', '').split():
                last_stroke = self._current_group.elements.pop()
                last_target = self._current_group.elements[-1]
            mask = self._dwg.defs.add(self._dwg.mask())
            mask.add(self._dwg.use(last_target.get_iri()))
            mask['color-interpolation'] = 'sRGB'
            self._clip_group = self._dwg.g(mask=mask.get_funciri())
            self._clip_group['class'] = 'clipping-mask'
            self._current_group.add(self._clip_group)
            self._clip_group.add(target)

            # Acutally clipping with mask and mix-blend-mode does not
            # correctly blend in SVG. clipPath does, but then cannot use
            # bitmap for clipping. Any workaround?
            self._clip_group['style'] = 'mix-blend-mode: {}'.format(
                blend_mode)
            if not self._clbl:
                self._clip_group.attribs['style'] += '; isolation: isolate;'

            if last_stroke:  # Move the stroke to the front.
                self._current_group.add(last_stroke)
        else:
            self._clip_group = None
            self._current_group.add(target)

            # Keep info for when next layer is clip group
            self._clbl = blocks.get(b'clbl')

        if vector_stroke:
            self._current_group.add(vector_stroke)

    def _get_target(self, layer):
        target = None
        if isinstance(layer, psd_tools.Group):
            # Group.
            current_group = self._current_group
            target = self._dwg.g()
            target.set_desc(title=_safe_utf8(layer.name))
            target['class'] = 'manual-group'
            self._current_group = target
            self._add_group(layer.layers)
            self._current_group = current_group
        elif _has_visible_pixels(layer._info):
            # Regular pixel layer.
            target = self._dwg.image(
                self._get_image_href(layer.as_PIL()),
                insert=(layer.bbox.x1, layer.bbox.y1),
                size=(layer.bbox.width, layer.bbox.height),
                debug=False)  # To disable attribute validation.
            target.set_desc(title=_safe_utf8(layer.name))

            text = self._get_text(layer)
            if text:
                if self.text_mode == 'text-only':
                    text.set_desc(title=_safe_utf8(layer.name))
                    target = text
                elif self.text_mode == 'image-only':
                    pass
                else:
                    target['class'] = 'text-image'
                    container = self._dwg.g()
                    container.elements.append(target.elements.pop(0))
                    container.add(target)
                    container.add(text)
                    container['class'] = 'text-container'
                    target = container
        elif _is_shape_layer(layer._info):
            blocks = layer._tagged_blocks
            vsms = blocks.get(b'vsms', blocks.get(b'vmsk'))
            anchors = [
                (p['anchor'][1] * self.width,
                 p['anchor'][0] * self.height)
                for p in vsms.path if p['selector'] in (1, 2)]
            fill = 'none'
            if b'SoCo' in blocks:
                items = dict(blocks[b'SoCo'].data.items)
                fill = self._get_color_in_item(items)
            target = self._dwg.polygon(points=anchors, fill=fill)
            target.set_desc(title=_safe_utf8(layer.name))
        else:
            target = self._get_adjustments(layer)
            if target:
                logger.debug('{} {}'.format(layer.name, target))
            else:
                logger.warning('Not rendered: {}'.format(layer))
            return None
        return target

    def _add_mask_if_exist(self, layer):
        mask_data = layer.mask_data
        if not mask_data or not mask_data.is_valid or \
                mask_data.mask_data.flags.mask_disabled:
            return None
        background_color = mask_data.mask_data.real_background_color
        if background_color is None:
            background_color = mask_data.background_color

        # In SVG, mask needs a default rect.
        default_bbox = layer.bbox
        if not default_bbox:
            default_bbox = psd_tools.BBox(0, 0, self.width, self.height)
        mask = self._dwg.defs.add(self._dwg.mask(
            size=(default_bbox.width, default_bbox.height)))
        mask.add(self._dwg.rect(
            insert=(default_bbox.x1, default_bbox.y1),
            size=(default_bbox.width, default_bbox.height),
            fill='rgb({0},{0},{0})'.format(background_color)))
        bbox = mask_data.bbox
        mask.add(self._dwg.image(
            self._get_image_href(mask_data.as_PIL()),
            size=(bbox.width, bbox.height),
            insert=(bbox.x1, bbox.y1)))
        mask['color-interpolation'] = 'sRGB'
        return mask

    def _get_opacity(self, layer):
        record = layer._info
        opacity = record.opacity / 255.0
        fill_opacity = dict(record.tagged_blocks).get(b'iOpa', 255) / 255.0
        return opacity, fill_opacity

    def _get_effects(self, layer):
        blocks = layer._tagged_blocks
        effects = blocks.get(
            b'lfx2', blocks.get(b'lfxs', blocks.get(b'lmfx', None)))
        enabled_effects = {}
        if effects:
            for key, info in effects.descriptor.items:
                if key == b'masterFXSwitch' and not info.value:
                    return None
                if isinstance(info, psd_tools.decoder.actions.List):
                    info = info.items[0]
                if not isinstance(info, psd_tools.decoder.actions.Descriptor):
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
            blend_mode = BLEND_MODE2.get(items[b'Md  '].value, 'normal')
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
            blend_mode = BLEND_MODE2.get(items[b'Md  '].value, 'normal')
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
            blend_mode = BLEND_MODE2.get(items[b'Md  '].value, 'normal')
        if blend_mode != 'normal':
            rect['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        return rect

    def _add_drsh(self, items, target_iri):
        blur = items[b'blur'].value
        blend_mode = BLEND_MODE2.get(items[b'Md  '].value, 'normal')

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
        blend_mode = BLEND_MODE2.get(items[b'Md  '].value, 'normal')
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
            blend_mode = BLEND_MODE2.get(items[b'Md  '].value, 'normal')
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
            blend_mode = BLEND_MODE2.get(items[b'Md  '].value, 'normal')
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
        blend_mode = BLEND_MODE2.get(items[b'Md  '].value, 'normal')
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
            else:
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
        if not b'Clrs' in grad_items:
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

    def _get_white_filter(self):
        if not self._white_filter:
            self._white_filter = self._dwg.defs.add(self._dwg.filter())
            self._white_filter['class'] = 'white-filter'
            self._white_filter.feColorMatrix(
                'SourceAlpha', type='matrix',
                values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0")
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

    def _get_vector_stroke(self, layer, target):
        blocks = layer._tagged_blocks
        if b'vstk' in blocks and (b'vsms' in blocks or b'vmsk' in blocks):
            vstk = dict(blocks[b'vstk'].data.items)
            if vstk.get(b'strokeEnabled').value:
                vsms = blocks.get(b'vsms', blocks.get(b'vmsk'))
                anchors = [
                    (p['anchor'][1] * self.width,
                     p['anchor'][0] * self.height)
                    for p in vsms.path if p['selector'] in (1, 2)]
                return self._add_vstk(vstk, anchors, target.get_iri(),
                                      layer.bbox)
        return None

    def _add_vstk(self, vstk, anchors, target_iri, bbox):
        line_style = vstk[b'strokeStyleLineAlignment'].value
        target = self._dwg.polygon(points=anchors, fill='none')

        stroke_width = int(vstk[b'strokeStyleLineWidth'].value)
        if line_style == b'strokeStyleAlignInside':
            clippath = self._dwg.defs.add(self._dwg.clipPath())
            clippath['class'] = 'stroke-inside'
            clippath.add(self._dwg.polygon(points=anchors))
            target['stroke-width'] = stroke_width * 2
            target['clip-path'] = clippath.get_funciri()
        elif line_style == b'strokeStyleAlignOutside':
            mask = self._dwg.defs.add(self._dwg.mask())
            mask['class'] = 'stroke-outside'
            mask.add(self._dwg.rect(
                insert=(bbox.x1, bbox.y1), size=(bbox.width, bbox.height),
                fill='white'))
            mask.add(self._dwg.polygon(points=anchors, fill='black'))
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

        blend_mode = BLEND_MODE2.get(
            vstk[b'strokeStyleBlendMode'].value, 'normal')
        if blend_mode != 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)

        return target

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
            if span[b'Text'] == '\r':
                newline = True
                continue
            value = _safe_utf8(span[b'Text'])
            tspan = self._dwg.tspan(value)
            if newline:
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
                rgb = [int(c*255) for c in span[b'FillColor'][b'Values'][1:]]
                opacity = span[b'FillColor'][b'Values'][0]
            else:
                rgb = (0, 0, 0)
                opacity = 1.0
            tspan['fill'] = 'rgb({},{},{})'.format(*rgb)
            tspan['fill-opacity'] = opacity

            text.add(tspan)
        return text

    def _get_adjustments(self, layer):
        target = None
        blocks = dict(layer._info.tagged_blocks)
        if b'brit' in blocks:
            cged = blocks.get(b'CgEd', None)
            if cged:
                cged = dict(cged.descriptor.items)
            target = self._dwg.g()
            target['class'] = 'adjustment brightness'
            target['filter'] = self._add_brightness(
                blocks[b'brit'], cged, layer)
        if b'expA' in blocks:
            target = self._dwg.g()
            target['class'] = 'adjustment exposure'
            target['filter'] = self._add_exposure(blocks[b'expA'], layer)
        if b'hue2' in blocks or b'hue ' in blocks:
            items = blocks.get(b'hue2', blocks.get(b'hue ', None))
            target = self._dwg.g()
            target['class'] = 'adjustment hue-saturation'
            target['filter'] = self._add_huesaturation(items, layer)
        if b'levl' in blocks:
            target = self._dwg.g()
            target['class'] = 'adjustment levels'
            # target['filter'] = self._add_levels(blocks[b'levl'], layer)
        if b'vibA' in blocks:
            target = self._dwg.g()
            target['class'] = 'adjustment vibrance'
            target['filter'] = self._add_vibrance(blocks[b'vibA'], layer)
        if b'curv' in blocks:
            target = self._dwg.g()
            target['class'] = 'adjustment curves'
            # target['filter'] = self._add_curves(blocks[b'curv'], layer)
        if target and target['class'].startswith('adjustment'):
            target.set_desc(title=_safe_utf8(layer.name))
            if layer._info.clipping:
                element = self._current_group.elements[-1]
                if not isinstance(element, svgwrite.container.Defs) and \
                        not isinstance(element, svgwrite.base.Title) and \
                        not isinstance(element, svgwrite.base.Desc):
                    child = self._current_group.elements.pop()
                    # Inherit child's blend mode.
                    if 'style' in child.attribs:
                        target['style'] = child['style']
                    target.add(child)
            else:
                stack = []
                for i in reversed(range(len(self._current_group.elements))):
                    element = self._current_group.elements[i]
                    if not isinstance(element, svgwrite.container.Defs) and \
                            not isinstance(element, svgwrite.base.Title) and \
                            not isinstance(element, svgwrite.base.Desc):
                        stack.append(self._current_group.elements.pop(i))
                while len(stack) > 0:
                    target.add(stack.pop())
            self._current_group.add(target)
        return target

    def _add_feimage_mask_if_exist(self, layer, filt, result):
        #
        # This applies masked adjustments to the graphics element.
        # Note that SVG filter cannot be applied to the background.
        #
        mask_data = layer.mask_data
        if not mask_data or not mask_data.is_valid or \
                mask_data.mask_data.flags.mask_disabled:
            return None

        image = mask_data.as_PIL()

        bbox = mask_data.bbox
        background_color = mask_data.mask_data.real_background_color
        if background_color is None:
            background_color = mask_data.background_color

        flood = filt.feFlood(result='maskBackground')
        flood['flood-color'] = 'rgb({0},{0},{0})'.format(background_color)
        filt.feImage(
            self._get_image_href(image), result='mask', x=bbox.x1, y=bbox.y1,
            width=bbox.width, height=bbox.height)
        filt.feComposite('mask', in2='maskBackground', operator='over',
                         result='maskFull')
        cm = filt.feColorMatrix(
            'maskFull', type='matrix', result='maskAlpha',
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0")
        cm['color-interpolation-filters'] = 'sRGB'
        filt.feComposite(result, in2='maskAlpha', operator='in',
                         result='maskedEffect')
        filt.feComposite('maskedEffect', in2='SourceGraphic',
                         operator='over')

    def _add_brightness(self, items, cged, layer):
        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'brightness'
        result = 'brightness'
        if cged:
            brightness = _get_signed_int32(cged[b'Brgh'].value)  # [-150, 150]
            contrast = _get_signed_int32(cged[b'Cntr'].value)  # [-50, 100]
            brightness = 2 ** (brightness / 150.0)
            contrast = contrast / 150.0
            means = cged[b'means'].value / 255.0
            lab = cged[b'Lab '].value
        else:
            brightness = 2 ** (items.brightness / 100.0)  # [-100, 100]
            contrast = items.contrast / 100.0  # [-100, 100]
            means = items.mean / 255.0
            lab = items.lab
        transfer = filt.feComponentTransfer(result='brit')
        transfer['color-interpolation-filters'] = 'sRGB'
        transfer.feFuncR('linear', slope=brightness)
        transfer.feFuncG('linear', slope=brightness)
        transfer.feFuncB('linear', slope=brightness)
        # Contrast seems second-order equation.
        transfer = filt.feComponentTransfer('brit', result=result)
        transfer['color-interpolation-filters'] = 'sRGB'
        transfer.feFuncR('linear', slope=1 + contrast,
                         intercept=-contrast * means)
        transfer.feFuncG('linear', slope=1 + contrast,
                         intercept=-contrast * means)
        transfer.feFuncB('linear', slope=1 + contrast,
                         intercept=-contrast * means)
        self._add_feimage_mask_if_exist(layer, filt, result)
        return filt.get_funciri()

    def _add_exposure(self, items, layer):
        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'exposure'
        exposure = 2 ** (items.exposure / 2)   # [-20, 20]
        gamma = - np.log(items.gamma) + 1.0    # [9.99,0.01]
        offset = 2 * items.offset              # [-0.5, 0.5]
        result = 'exposure'
        transfer = filt.feComponentTransfer(result=result)
        transfer['color-interpolation-filters'] = 'sRGB'
        transfer.feFuncR('gamma', amplitude=exposure,
                         offset=offset, exponent=gamma)
        transfer.feFuncG('gamma', amplitude=exposure,
                         offset=offset, exponent=gamma)
        transfer.feFuncB('gamma', amplitude=exposure,
                         offset=offset, exponent=gamma)
        transfer.feFuncA('identity')
        self._add_feimage_mask_if_exist(layer, filt, result)
        return filt.get_funciri()

    def _add_levels(self, items, layer):
        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'levels'
        result = 'levels'
        transfer = filt.feComponentTransfer(result=result)
        transfer['color-interpolation-filters'] = 'sRGB'
        transfer.feFuncR('identity')
        transfer.feFuncG('identity')
        transfer.feFuncB('identity')
        transfer.feFuncA('identity')
        #
        # TODO: Implement levels adjustment.
        #
        self._add_feimage_mask_if_exist(layer, filt, result)
        return filt.get_funciri()

    def _add_huesaturation(self, items, layer):
        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'hue-saturation'
        result = 'hsl'
        hue = items.master[0]
        saturation = (items.master[1] + 100.0) / 100.0
        lightness = items.master[2] / 100.0
        filt.feColorMatrix(type='hueRotate', values='{}'.format(hue),
                           result='hue')
        filt.feColorMatrix('hue', type='saturate',
                           values='{}'.format(saturation),
                           result='saturation')
        transfer = filt.feComponentTransfer(result=result)
        transfer['color-interpolation-filters'] = 'sRGB'
        if lightness < 0:
            transfer.feFuncR('linear', slope=lightness + 1, intercept=0)
            transfer.feFuncG('linear', slope=lightness + 1, intercept=0)
            transfer.feFuncB('linear', slope=lightness + 1, intercept=0)
        else:
            transfer.feFuncR('linear', slope=1, intercept=lightness)
            transfer.feFuncG('linear', slope=1, intercept=lightness)
            transfer.feFuncB('linear', slope=1, intercept=lightness)
        self._add_feimage_mask_if_exist(layer, filt, result)
        return filt.get_funciri()

    def _add_vibrance(self, items, layer):
        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'vibrance'
        items = dict(items.descriptor.items)
        vibrance = items.get(b'vibrance', None)
        result = 'vibrance'
        if vibrance:
            vibrance = _get_signed_int32(vibrance.value) / 180.0 + 1.0
            matrix = filt.feColorMatrix(type='saturate', values=vibrance,
                                        result=result)
            matrix['color-interpolation-filters'] = 'sRGB'
        saturation = items.get(b'Strt', None)
        if saturation:
            result = 'saturation'
            saturation = (_get_signed_int32(saturation.value) + 100) / 100.0
            matrix = filt.feColorMatrix(type='saturate', values=saturation,
                                        result=result)
            matrix['color-interpolation-filters'] = 'sRGB'
        if not vibrance and not saturation:
            matrix = filt.feColorMatrix(type='saturate', values=1.0,
                                        result=result)
        self._add_feimage_mask_if_exist(layer, filt, result)
        return filt.get_funciri()

    def _add_curves(self, items, layer):
        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'curves'
        result = 'curves'
        transfer = filt.feComponentTransfer(result=result)
        transfer['color-interpolation-filters'] = 'sRGB'
        transfer.feFuncR('identity')
        transfer.feFuncG('identity')
        transfer.feFuncB('identity')
        transfer.feFuncA('identity')
        #
        # TODO: Implement cuves adjustment.
        #
        self._add_feimage_mask_if_exist(layer, filt, result)
        return filt.get_funciri()


def _safe_utf8(text):
    return ILLEGAL_XML_RE.sub(' ', text)


def _get_signed_int32(value):
    INT32_MAX = (1 << 31)
    if value >= INT32_MAX:
        value -= (1 << 32)
    return value


def _has_visible_pixels(record):
    return (record.bottom - record.top > 0 and
            record.right - record.left > 0)


def _is_shape_layer(record):
    blocks = dict(record.tagged_blocks)
    return (b'vmsk' in blocks or b'vsms' in blocks) and b'vogk' in blocks


def _get_text_info(layer):
    type_info = dict(layer._info.tagged_blocks).get(b'TySh', None)
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
