# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
import numpy as np
import svgwrite
from psd_tools.constants import TaggedBlockID
from psd_tools.api.effects import (
    OuterGlow, InnerGlow, DropShadow, InnerShadow, ColorOverlay,
    PatternOverlay, GradientOverlay, BevelEmboss, Satin, Stroke
)
from psd2svg.converter.constants import BLEND_MODE
from psd2svg.utils.color import cmyk2rgb


logger = getLogger(__name__)


class EffectsConverter(object):

    def add_effects(self, layer, element):
        """
        Add effects to the element.

        Effects wraps the given element in a group, and the group will contain
        multiple items each corresponding to the applied effect.
        """

        fill_opacity = layer.tagged_blocks.get_data(
            TaggedBlockID.BLEND_FILL_OPACITY, 255
        ) / 255.0
        if len(layer.effects) == 0:
            # if fill_opacity < 1.0:
            #     element['opacity'] = layer.opacity / 255.0 * fill_opacity
            return element
        else:
            container = self._dwg.g()
            container['class'] = 'psd-effects'
            # Move class annotation.
            if 'class' in element.attribs:
                container['class'] += ' ' + element.attribs['class']
                del element.attribs['class']
            # Move subclass of title nodes.
            for child in element.elements:
                if isinstance(child, svgwrite.base.Title):
                    container.add(child)
            for child in container.elements:
                element.elements.remove(child)
            self._dwg.defs.add(element)


        # Outer effects.
        for effect in layer.effects:
            if isinstance(effect, DropShadow):
                shadow = self.create_drop_shadow(layer, effect, element)
                container.add(shadow)
        for effect in layer.effects:
            if isinstance(effect, OuterGlow):
                glow = self.create_outer_glow(layer, effect, element)
                container.add(glow)

        blend_mode = None  # Interior blend mode.
        if layer.tagged_blocks.get_data(
            TaggedBlockID.BLEND_INTERIOR_ELEMENTS, False
        ):
            blend_mode = layer.blend_mode

        # Add the original.
        use = self._dwg.use(element.get_iri(), opacity=fill_opacity)
        use['class'] = 'layer-effect original'
        container.add(use)

        # Overlay effects.
        if any(
            isinstance(effect, (
                PatternOverlay, GradientOverlay, ColorOverlay
            ))
            for effect in layer.effects
        ):
            mask = self._create_overlay_mask(layer, element)
            for effect in layer.effects:
                if isinstance(effect, PatternOverlay):
                    overlay = self.create_pattern_overlay(
                        layer, effect, mask, blend_mode
                    )
                    container.add(overlay)

            for effect in layer.effects:
                if isinstance(effect, GradientOverlay):
                    overlay = self.create_gradient_overlay(
                        layer, effect, mask, blend_mode
                    )
                    container.add(overlay)

            for effect in layer.effects:
                if isinstance(effect, ColorOverlay):
                    overlay = self.create_color_overlay(
                        layer, effect, mask, blend_mode
                    )
                    container.add(overlay)

        # Inner effects.
        for effect in layer.effects:
            if isinstance(effect, InnerShadow):
                shadow = self.create_inner_shadow(
                    layer, effect, element, blend_mode
                )
                container.add(shadow)

        for effect in layer.effects:
            if isinstance(effect, InnerGlow):
                glow = self.create_inner_glow(
                    layer, effect, element, blend_mode
                )
                container.add(glow)

        # Bevel and emboss.
        for effect in layer.effects:
            if isinstance(effect, BevelEmboss):
                bevelemboss = self.create_bevel_emboss(
                    layer, effect, element
                )
                container.add(bevelemboss)

        # Satin.
        for effect in layer.effects:
            if isinstance(effect, Satin):
                satin = self.create_satin(layer, effect, element)
                container.add(satin)

        # Stroke.
        for effect in layer.effects:
            if isinstance(effect, Stroke):
                stroke = self.create_stroke(layer, effect, element)
                container.add(stroke)

        return container

    def _create_overlay_mask(self, layer, element):
        """Create a mask used for overlay effects."""
        if layer.width == 0 or layer.height == 0:
            logger.warning('Fill effect to empty layer.')

        mask_element = self._dwg.defs.add(self._dwg.mask(
            size=(layer.width, layer.height)))
        mask_element['color-interpolation'] = 'sRGB'
        use = mask_element.add(self._dwg.use(element.get_iri()))
        use['filter'] = self._get_white_filter().get_funciri()
        return mask_element

    def create_color_overlay(self, layer, effect, mask, blend_mode):
        """Create a color overlay."""
        element = self._dwg.rect(
            size=(layer.width, layer.height),
            insert=(layer.left, layer.top),
            fill=self.create_solid_color(effect.value['Clr ']),
            mask=mask.get_funciri())
        self._add_overlay_attribute(
            element, effect, blend_mode, 'color-overlay')
        return element

    def create_pattern_overlay(self, layer, effect, mask, blend_mode):
        """Create a pattern overlay."""
        pattern = self.create_pattern(effect.value, (layer.left, layer.top))
        element = self._dwg.rect(
            size=(layer.width, layer.height),
            insert=(layer.left, layer.top),
            fill=pattern.get_funciri(),
            mask=mask.get_funciri())
        self._add_overlay_attribute(
            element, effect, blend_mode, 'pattern-overlay')
        return element

    def create_gradient_overlay(self, layer, effect, mask, blend_mode):
        """Create a gradient overlay."""
        gradient = self.create_gradient(
            effect.value, (layer.width, layer.height)
        )
        element = self._dwg.rect(
            size=(layer.width, layer.height),
            insert=(layer.left, layer.top),
            fill=gradient.get_funciri() if gradient else 'none',
            mask=mask.get_funciri())
        self._add_overlay_attribute(
            element, effect, blend_mode, 'gradient-overlay')
        return element

    def _add_overlay_attribute(self, element, effect, blend_mode, kind):
        """Add common overlay attributes."""
        element['class'] = 'layer-effect {}'.format(kind)
        opacity = effect.opacity / 100.0  # TODO: Check unit
        if opacity < 1.0:
            element['fill-opacity'] = opacity
        self.add_blend_mode(
            element, blend_mode if blend_mode else effect.blend_mode)

    def create_drop_shadow(self, layer, effect, element):
        """Create a drop shadow effect."""
        blur = effect.size
        spread = effect.choke / 100.0
        angle = effect.angle
        radius = effect.distance
        dx = -radius * np.cos(np.radians(angle))
        dy = radius * np.sin(np.radians(angle))
        filt = self._dwg.defs.add(self._dwg.filter(
            x='-50%', y='-50%', size=('200%', '200%')))
        filt['class'] = 'drop-shadow'

        filt.feOffset('SourceAlpha', dx=dx, dy=dy, result='drshOffset')
        filt.feGaussianBlur('drshOffset', stdDeviation=blur / 2.0,
                            result='drshBlur',
                            **{'color-interpolation-filters': 'sRGB'})
        transfer = filt.feComponentTransfer('drshBlur', result='drshBlurA')
        transfer.feFuncA('linear', slope=1.0 + 4 * spread, intercept=0.0)
        flood = filt.feFlood(result='drshFlood')
        flood['flood-color'] = self.create_solid_color(effect.value['Clr '])
        flood['flood-opacity'] = effect.opacity / 100.0
        filt.feComposite('drshFlood', in2='drshBlurA', operator='in',
                         result='drshShadow')

        shadow = self._dwg.use(element.get_iri(), filter=filt.get_funciri())
        shadow['class'] = 'layer-effect dropshadow'
        self.add_blend_mode(shadow, effect.blend_mode)
        return shadow

    def create_outer_glow(self, layer, effect, element):
        """Create an outer glow effect."""
        blur = effect.size
        spread = effect.choke / 100.0
        filt = self._dwg.defs.add(self._dwg.filter(
            x='-50%', y='-50%', size=('200%', '200%')))
        filt['class'] = 'outerglow'

        # Saturate alpha mask before glow if non-zero spread.
        if spread > 0:
            transfer = filt.feComponentTransfer(
                'SourceAlpha', result='orglAlpha')
            transfer.feFuncA('linear', slope=255, intercept=0.0)
            result = 'orglDilate'
            filt.feMorphology(
                'orglAlpha', radius=blur * spread, operator='dilate',
                result=result)
        else:
            result = 'SourceAlpha'
        filt.feGaussianBlur(
            result, stdDeviation=blur * (1 - spread), result='orglBlur',
            **{'color-interpolation-filters': 'sRGB'})
        transfer = filt.feComponentTransfer('orglBlur', result='orglBlurA')
        transfer.feFuncA('linear', slope=1 + 4 * spread, intercept=0.0)
        flood = filt.feFlood(result='orglFlood')

        if effect.color:
            flood['flood-color'] = self.create_solid_color(
                effect.value['Clr ']
            )
        else:
            logger.warning("Gradient glow not implemented")
            flood['flood-color'] = self.create_solid_color(
                effect.value['Grad']['Clrs'][0]['Clr ']
            )
        flood['flood-opacity'] = effect.opacity / 100.0
        filt.feComposite('orglFlood', in2='orglBlurA', operator='in',
                         result='orglShadow')
        filt.feComposite('orglShadow', in2='SourceAlpha', operator='out',
                         result='orglShadowA')

        glow = self._dwg.use(element.get_iri(), filter=filt.get_funciri())
        glow['class'] = 'layer-effect outer-glow'
        self.add_blend_mode(glow, effect.blend_mode)
        return glow

    def create_inner_shadow(self, layer, effect, element, blend_mode):
        """Create inner shadow effect."""
        blur = effect.size
        angle = effect.angle
        radius = effect.distance
        dx = -radius * np.cos(np.radians(angle))
        dy = radius * np.sin(np.radians(angle))

        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'inner-shadow'
        flood = filt.feFlood(result='irshFlood')
        flood['flood-color'] = self.create_solid_color(effect.value['Clr '])
        flood['flood-opacity'] = effect.opacity / 100.0
        filt.feComposite('irshFlood', in2='SourceAlpha', operator='out',
                         result='irshShadow')
        filt.feOffset('irshShadow', dx=dx, dy=dy, result='irshOffset')
        filt.feGaussianBlur('irshOffset', stdDeviation=blur / 2.0,
                            result='irshBlur',
                            **{'color-interpolation-filters': 'sRGB'})
        filt.feComposite('irshBlur', in2='SourceAlpha', operator='in',
                         result='irshShadow')

        shadow = self._dwg.use(element.get_iri(), filter=filt.get_funciri())
        shadow['class'] = 'layer-effect inner-shadow'
        self.add_blend_mode(
            shadow, blend_mode if blend_mode else effect.blend_mode)
        return shadow

    def create_inner_glow(self, layer, effect, element, blend_mode):
        """Create inner glow effect."""
        blur = effect.size
        spread = effect.choke / 100.0

        # Real inner glow needs distance transform.
        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'inner-glow'
        flood = filt.feFlood(result='irglFlood')
        # TODO: Gradient fill
        if effect.color:
            flood['flood-color'] = color = self.create_solid_color(
                effect.value['Clr ']
            )
        else:
            logger.warning("Gradient glow not implemented")
        flood['flood-opacity'] = effect.opacity / 100.0
        # Saturate alpha mask before glow.
        transfer = filt.feComponentTransfer('SourceAlpha', result='irglAlpha')
        transfer.feFuncA('linear', slope=255, intercept=0)
        filt.feComposite('irglFlood', in2='irglAlpha', operator='out',
                         result='irglShadow')
        filt.feMorphology('irglShadow', radius=blur * spread,
                          operator='dilate', result='irglDilate')
        filt.feGaussianBlur('irglDilate', stdDeviation=blur * (1 - spread),
                            result='irglBlur',
                            **{'color-interpolation-filters': 'sRGB'})
        filt.feComposite('irglBlur', in2='irglAlpha', operator='in',
                         result='irglShadow')

        glow = self._dwg.use(element.get_iri(), filter=filt.get_funciri())
        glow['class'] = 'layer-effect inner-glow'
        self.add_blend_mode(
            glow, blend_mode if blend_mode else effect.blend_mode)
        return glow

    def create_bevel_emboss(self, layer, effect, element):
        """Create bevel and emboss effect."""
        # In SVG, bevel and emboss need to be split into two elements.

        # Shadow.
        filt = self._dwg.defs.add(self._dwg.filter())
        shadow = self._dwg.use(
            element.get_iri(), filter=filt.get_funciri())
        shadow['class'] = 'layer-effect bevel-emboss shadow'
        shadow['opacity'] = effect.shadow_opacity / 100.0
        self.add_blend_mode(shadow, effect.shadow_mode)
        filt['class'] = 'bevel-emboss shadow'
        if effect.bevel_style == 'inner-bevel':
            blur = filt.feGaussianBlur('SourceAlpha', result='blur',
                stdDeviation=effect.size / 2.0,
                **{'color-interpolation-filters': 'sRGB'})
            light = filt.feDiffuseLighting('blur',
                result='shadow',
                surfaceScale=effect.size / 2.0,
                diffuseConstant=2.0)
            light.feDistantLight(azimuth=-effect.angle,
                                 elevation=effect.altitude)
            color = [(x / 255.0) for x in effect.shadow_color.values()]
            filt.feColorMatrix(
                'shadow',
                result='color-shadow',
                type='matrix',
                values="0 0 0 0 {:g} 0 0 0 0 {:g} "
                       "0 0 0 0 {:g} -1.0 0 0 0 1.0".format(*color))
            filt.feComposite('color-shadow', in2='SourceAlpha', operator='in')
        elif effect.bevel_style == 'emboss':
            filt['x'], filt['y'] = '-10%', '-10%'
            filt['width'], filt['height'] = '120%', '120%'
            blur = filt.feGaussianBlur('SourceAlpha', result='blur',
                stdDeviation=effect.size / 3.2,
                **{'color-interpolation-filters': 'sRGB'})
            light = filt.feDiffuseLighting('blur',
                result='shadow',
                surfaceScale=effect.size / 1.2,
                diffuseConstant=2.0)
            light.feDistantLight(azimuth=-effect.angle,
                                 elevation=effect.altitude)
            color = [(x / 255.0) for x in effect.shadow_color.values()]
            filt.feColorMatrix(
                'shadow',
                result='color-shadow',
                type='matrix',
                values="0 0 0 0 {:g} 0 0 0 0 {:g} "
                       "0 0 0 0 {:g} -1.0 0 0 0 1.0".format(*color))
        else:
            logger.warning("Bevel style not implemented: {}".format(
                effect.bevel_style
            ))

        # Highlight.
        filt = self._dwg.defs.add(self._dwg.filter())
        highlight = self._dwg.use(
            element.get_iri(), filter=filt.get_funciri())
        highlight['class'] = 'layer-effect bevel-emboss highlight'
        highlight['opacity'] = effect.highlight_opacity / 100.0
        self.add_blend_mode(highlight, effect.highlight_mode)
        filt['class'] = 'bevel-emboss highlight'
        if effect.bevel_style == 'inner-bevel':
            blur = filt.feGaussianBlur('SourceAlpha', result='blur',
                stdDeviation=effect.size / 2.0,
                **{'color-interpolation-filters': 'sRGB'})
            light = filt.feSpecularLighting('blur',
                result='highlight',
                surfaceScale=effect.size / 1.6,
                specularExponent=14.0,
                specularConstant=1.0)
            light.feDistantLight(azimuth=-effect.angle,
                                 elevation=effect.altitude)
            light['lighting-color'] = self.create_solid_color(
                effect.highlight_color)
            filt.feComposite('highlight', in2='SourceAlpha', operator='in')
        elif effect.bevel_style == 'emboss':
            filt['x'], filt['y'] = '-10%', '-10%'
            filt['width'], filt['height'] = '120%', '120%'
            blur = filt.feGaussianBlur('SourceAlpha', result='blur',
                stdDeviation=effect.size / 3.2,
                **{'color-interpolation-filters': 'sRGB'})
            light = filt.feSpecularLighting('blur',
                result='highlight',
                surfaceScale=effect.size / 3.2,
                specularExponent=14.0,
                specularConstant=1.0)
            light.feDistantLight(azimuth=-effect.angle,
                                 elevation=effect.altitude)
            light['lighting-color'] = self.create_solid_color(
                effect.highlight_color)
        else:
            logger.warning("Bevel style not implemented: {}".format(
                effect.bevel_style
            ))

        container = self._dwg.g()
        container.add(shadow)
        container.add(highlight)
        container['class'] = 'layer-effect bevel-emboss'
        return container

    def create_satin(self, layer, effect, element):
        """Create satin effect."""

        """
        Sating effect is complicated to reproduce:

        1. Create two shifted self-shapes from two sides, where the
           shift arrangement is determined from the angle parameter and
           distance. The two shape masks should follow even-odd filling rule.
        2. Invert the filled area if inverted.
        3. Apply Gaussian blur to the filled area from the two rectangles.
        4. For the filled area, apply specified color and opacity.
        """
        angle = effect.angle
        radius = effect.distance
        dx = -radius * np.cos(np.radians(angle))
        dy = radius * np.sin(np.radians(angle))

        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'satin'
        filt.feOffset('SourceAlpha', result='shape1', dx=dx, dy=dy)
        filt.feOffset('SourceAlpha', result='shape2', dx=-dx, dy=-dy)
        filt.feComposite('shape1', in2='shape2', result='xor', operator='xor')
        color = [x / 255.0 for x in effect.color.values()]
        if effect.inverted:
            filt.feColorMatrix(
                'xor',
                result='xor-shaded',
                type='matrix',
                values='1 0 0 0 {:g} '
                       '0 1 0 0 {:g} '
                       '0 0 1 0 {:g} '
                       '0 0 0 -1 1 '.format(*color),
                )
        else:
            filt.feColorMatrix(
                'xor',
                result='xor-shaded',
                type='matrix',
                values='1 0 0 0 {:g} '
                       '0 1 0 0 {:g} '
                       '0 0 1 0 {:g} '
                       '0 0 0 1 0 '.format(*color),
                )
        filt.feGaussianBlur('xor-shaded', result='blur',
            stdDeviation=effect.size / 2.0,
            **{'color-interpolation-filters': 'sRGB'})
        filt.feComposite('blur', in2='SourceAlpha', operator='in')

        satin = self._dwg.use(
            element.get_iri(), filter=filt.get_funciri())
        satin['class'] = 'layer-effect satin'
        satin['opacity'] = effect.opacity / 100.0

        self.add_blend_mode(satin, effect.blend_mode)
        return satin

    def create_stroke(self, layer, effect, element):
        """Create a stroke effect."""
        radius = int(effect.size)  # TODO: Check unit.
        style = effect.position

        filt = self._dwg.defs.add(self._dwg.filter())
        filt['class'] = 'stroke'
        flood = filt.feFlood(result='frfxFlood')
        # TODO: Implement gradient or pattern fill
        if effect.fill_type == 'solid-color':
            flood['flood-color'] = self.create_solid_color(
                effect.value['Clr ']
            )
        elif effect.fill_type == 'pattern-overlay':
            logger.warning("Pattern stroke not implemented")
        elif effect.fill_type == 'gradient-overlay':
            logger.warning("Gradient stroke not implemented")
            grad = effect.value['Grad']
            if 'Clrs' in grad:
                flood['flood-color'] = self.create_solid_color(
                    grad['Clrs'][0]['Clr ']
                )
        else:
            logger.warning("Unknown fill type: {}".format(effect.fill_type))


        flood['flood-opacity'] = effect.opacity / 100.0
        if style == 'outer':
            filt.feMorphology('SourceAlpha', result='frfxMorph',
                              operator='dilate', radius=radius)
            filt.feComposite('frfxFlood', in2='frfxMorph', operator='in',
                             result='frfxBoundary')
            filt.feComposite('frfxBoundary', in2='SourceAlpha',
                             operator='out')
        elif style == 'inner':
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

        stroke = self._dwg.use(element.get_iri(), filter=filt.get_funciri())
        stroke['class'] = 'layer-effect stroke'
        self.add_blend_mode(stroke, effect.blend_mode)
        return stroke

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
