# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
from psd_tools.constants import TaggedBlock
from psd2svg.utils.xml import safe_utf8
import numpy as np
import svgwrite


logger = getLogger(__name__)


"""
Adjustment conversion is a bit tricky due to the poor support of
``BackgroundImage`` and ``BackgroundAlpha`` specification in most of the
renderers. Also CSS's `backdrop-filter` is not available in SVG.

The possible workaround is to wrap ALL elements appearing before the
adjustment in a group, and apply a filter to the group. This is not
perfect as the transparent background still does not get the filter effect.
The conversion is like the following.

In PSD::

    <psdimage>
        <pixel name="Background">
        <pixel name="Layer-1">
        <adjustment name="Adjustment-1">
        <adjustment name="Adjustment-2">
        <pixel name="Layer-2">

In SVG::

    <svg>
        <defs>
            <filter id="Adjustment-1"></filter>
            <filter id="Adjustment-2"></filter>
        </defs>

        <g filter="url(#Adjustment-2)">
            <g filter="url(#Adjustment-1)">
                <image id="Background"></image>
                <image id="Layer-1"></image>
            </g>
        </g>
        <image id="Layer-2"></image>
    </svg>


In a ideal situation where ``BackgroundImage`` is available, the following
conversion should work.

In SVG::

    <svg enable-background="new">
        <defs>
            <filter id="Adjustment-1"></filter>
            <filter id="Adjustment-2"></filter>
        </defs>

        <image id="Background"></image>
        <image id="Layer-1"></image>
        <g filter="url(#Adjustment-1)" />
        <g filter="url(#Adjustment-2)" />
        <image id="Layer-2"></image>
    </svg>

"""


class AdjustmentsConverter(object):

    def create_adjustment(self, layer):
        # self._dwg['enable-background'] = 'new'
        adjustment = layer.data
        if adjustment.name == "coloroverlay":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "patternoverlay":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "gradientoverlay":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "blackwhite":
            return self.create_blackwhite(adjustment)
        elif adjustment.name == "brightnesscontrast":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "channelmixer":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "colorbalance":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "colorlookup":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "curves":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "exposure":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "gradientmap":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "huesaturation":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "invert":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "levels":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "photofilter":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "posterize":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "selectivecolor":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "threshold":
            logger.warning("adjustment not implemented {}".format(adjustment))
        elif adjustment.name == "vibrance":
            logger.warning("adjustment not implemented {}".format(adjustment))
        else:
            logger.error("Unknown adjustment {}".format(adjustment))

        return self._dwg.g()


    def create_blackwhite(self, adjustment):
        filt = self._dwg.defs.add(self._dwg.filter())
        filt.feColorMatrix(
            'SourceImage',
            type='matrix',
            result='result',
            values='0.333 0.333 0.333 0 0 '
                   '0.333 0.333 0.333 0 0 '
                   '0.333 0.333 0.333 0 0 '
                   '0 0 0 1 0 ')
        container = self._dwg.g(filter=filt.get_funciri())
        return container


    def add_brightnesscontrast(self, adjustment, element):
        pass


    def _get_adjustments(self, layer):
        target = None
        blocks = dict(layer._record.tagged_blocks)
        for key in set.union(TaggedBlock._ADJUSTMENT_KEYS,
                             TaggedBlock._FILL_KEYS):
            if key in blocks:
                target = self._dwg.g()
                target['class'] = 'adjustment'

        if b'brit' in blocks:
            cged = blocks.get(b'CgEd', None)
            if cged:
                cged = dict(cged.descriptor.items)
            target['class'] = 'adjustment brightness'
            target['filter'] = self._add_brightness(
                blocks[b'brit'], cged, layer)
        if b'expA' in blocks:
            target['class'] = 'adjustment exposure'
            target['filter'] = self._add_exposure(blocks[b'expA'], layer)
        if b'hue2' in blocks or b'hue ' in blocks:
            items = blocks.get(b'hue2', blocks.get(b'hue ', None))
            target['class'] = 'adjustment hue-saturation'
            target['filter'] = self._add_huesaturation(items, layer)
        if b'levl' in blocks:
            target['class'] = 'adjustment levels'
            # target['filter'] = self._add_levels(blocks[b'levl'], layer)
        if b'vibA' in blocks:
            target['class'] = 'adjustment vibrance'
            target['filter'] = self._add_vibrance(blocks[b'vibA'], layer)
        if b'curv' in blocks:
            target['class'] = 'adjustment curves'
            # target['filter'] = self._add_curves(blocks[b'curv'], layer)
        if target and target['class'].startswith('adjustment'):
            target.set_desc(title=safe_utf8(layer.name))
            if layer._record.clipping:
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
        mask_data = layer.mask
        if not mask_data or not mask_data.is_valid() or \
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
        transfer = filt.feComponentTransfer('saturation', result=result)
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


def _get_signed_int32(value):
    INT32_MAX = (1 << 31)
    if value >= INT32_MAX:
        value -= (1 << 32)
    return value
