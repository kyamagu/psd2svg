# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
from psd_tools.user_api import BBox
from psd_tools.constants import TaggedBlock

from psd2svg.converter.constants import BLEND_MODE
from psd2svg.utils.xml import safe_utf8


logger = getLogger(__name__)


class LayerConverter(object):

    def _add_group(self, layers):
        for layer in reversed(layers):
            self._add_layer(layer)
            for clip in reversed(layer.clip_layers):
                self._add_layer(clip)

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
        if not layer.visible:
            target['visibility'] = 'hidden'
            if vector_stroke:
                vector_stroke['visibility'] = 'hidden'
        blend_mode = BLEND_MODE.get(layer.blend_mode, 'normal')
        if not blend_mode == 'normal':
            target['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        opacity, fill_opacity = self._get_opacity(layer)
        if opacity < 1.0:
            target['opacity'] = opacity

        if not effects and fill_opacity < 1.0:
            target['opacity'] = opacity * fill_opacity

        # TODO: Filter to strokes requires a different approach.
        blocks = layer.tagged_blocks

        if effects:
            interior_blend_mode = None
            if blocks.get(b'infx', False):
                interior_blend_mode = blend_mode
            target = self._add_effects(effects, layer, target, fill_opacity,
                                       interior_blend_mode)

        if (layer != self._input_layer and
                layer._record.clipping and self._clip_group):
            self._clip_group.add(target)

            # Acutally clipping with mask and mix-blend-mode does not
            # correctly blend in SVG. clipPath does, but then cannot use
            # bitmap for clipping. Any workaround?
            self._clip_group['style'] = 'mix-blend-mode: {}'.format(
                blend_mode)
            if not self._clbl:
                self._clip_group.attribs['style'] += '; isolation: isolate;'

        elif layer != self._input_layer and layer._record.clipping:
            # Convert the last target to a clipping mask
            last_stroke = None
            last_target = self._current_group.elements[-1]
            if 'vector-stroke' in last_target.attribs.get(
                    'class', '').split():
                last_stroke = self._current_group.elements.pop()
                last_target = self._current_group.elements[-1]
            mask = self._dwg.defs.add(self._dwg.mask())
            mask_bbox = layer.bbox

            use = self._dwg.use(last_target.get_iri())
            use['filter'] = self._get_white_filter().get_funciri()
            mask.add(use)

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
        if layer.is_group():
            # Group.
            current_group = self._current_group
            target = self._dwg.g()
            target.set_desc(title=safe_utf8(layer.name))
            target['class'] = 'manual-group'
            self._current_group = target
            self._add_group(layer.layers)
            self._current_group = current_group
        elif layer.has_pixels():
            # Regular pixel layer.
            target = self._dwg.image(
                self._get_image_href(layer.as_PIL()),
                insert=(layer.bbox.x1, layer.bbox.y1),
                size=(layer.bbox.width, layer.bbox.height),
                debug=False)  # To disable attribute validation.
            target.set_desc(title=safe_utf8(layer.name))

            text = self._get_text(layer)
            if text:
                text['class'] = 'text-text'
                if self.text_mode == 'text-only':
                    text.set_desc(title=safe_utf8(layer.name))
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
        elif layer.kind == 'shape':
            blocks = layer.tagged_blocks
            vsms = blocks.get(b'vsms', blocks.get(b'vmsk'))
            anchors = [
                (p['anchor'][1] * self.width,
                 p['anchor'][0] * self.height)
                for p in vsms.path if p['selector'] in (1, 2, 4, 5)]
            fill = self._get_fill(layer)
            target = self._dwg.polygon(points=anchors, fill=fill)
            target.set_desc(title=safe_utf8(layer.name))
        else:
            target = self._get_adjustments(layer)
            if target:
                logger.debug('{} {}'.format(layer.name, target))
            else:
                logger.warning('Not rendered: {}'.format(layer))
            return None
        return target

    def _add_mask_if_exist(self, layer):
        mask_data = layer.mask
        if not mask_data or not mask_data.is_valid() or \
                mask_data.mask_data.flags.mask_disabled:
            return None
        background_color = mask_data.mask_data.real_background_color
        if background_color is None:
            background_color = mask_data.background_color

        # In SVG, mask needs a default rect.
        default_bbox = layer.bbox
        if not default_bbox:
            default_bbox = BBox(0, 0, self.width, self.height)
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
        opacity = layer.opacity / 255.0
        fill_opacity = layer.get_tag(b'iOpa', 255) / 255.0
        return opacity, fill_opacity

    def _add_photoshop_view(self):
        # Embed original photoshop view.
        image = self._psd.as_PIL()
        original = self._dwg.add(self._dwg.image(
            self._get_image_href(image), insert=(0, 0),
            size=(self.width, self.height), visibility='hidden'))
        original['class'] = 'photoshop-image'
