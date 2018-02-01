# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
from psd_tools.user_api import BBox
from psd_tools.constants import TaggedBlock

from psd2svg.converter.constants import BLEND_MODE
from psd2svg.utils.xml import safe_utf8


logger = getLogger(__name__)


class LayerConverter(object):

    def convert_layer(self, layer):
        """Convert the given layer"""
        if layer.is_group():
            element = self.create_group(layer)

        elif layer.has_relevant_pixels():
            element = self.create_image(layer)
            if layer.kind == 'type':
                # TODO: Embed text metadata.
                # text = self._get_text(layer)
                pass
            if layer.kind == 'shape':
                # TODO: Embed vector graphics.
                pass

        else:
            # Boxless element is either shape fill or adjustment.
            # element = self._get_adjustments(layer)
            element = self.create_shape(layer)

        # TODO: vector stroke.
        # self._get_vector_stroke(layer, target)

        element = self.add_attributes(layer, element)
        mask_element = self.create_mask(layer)
        if mask_element and not layer.mask.disabled:
            element['mask'] = mask_element.get_funciri()

        element = self.add_effects(layer, element)
        return element

    def create_group(self, group, element=None):
        """Create and fill in a new group element."""
        if not element:
            element = self._dwg.g()
        for child_layer in reversed(group.layers):
            child_element = self.convert_layer(child_layer)
            element.add(child_element)

            # Clipping.
            if len(child_layer.clip_layers) > 0:
                clip_group = self.create_clipping(child_layer, child_element)
                element.add(clip_group)

                # TODO: Blending option.
                # layer.get_tag(TaggedBlock.BLEND_CLIPPING_ELEMENTS)
        return element

    def create_image(self, layer):
        """Create a pixel object."""
        element = self._dwg.image(
            self._get_image_href(layer.as_PIL()),
            insert=(layer.left, layer.top),
            size=(layer.width, layer.height),
            debug=False)  # To disable attribute validation.
        return element

    def create_shape(self, layer):
        """Create an adjustment element."""
        if layer.has_box():
            element = self._dwg.rect(
                insert=(layer.left, layer.top),
                size=(layer.width, layer.height),
                fill="none")
        else:
            element = self._dwg.rect(
                insert=(self._psd.bbox.x1, self._psd.bbox.y1),
                size=(self._psd.bbox.width, self._psd.bbox.height),
                fill="none")
        # TODO: Create a backdrop-filter.
        return element

    def create_mask(self, layer):
        """Create a mask."""
        if not layer.has_mask() or not layer.mask.has_box():
            return None

        # In SVG, mask needs a default rect.
        viewbox = layer.bbox
        if viewbox.is_empty():
            viewbox = BBox(0, 0, self.width, self.height)
        mask_element = self._dwg.defs.add(self._dwg.mask(
            size=(viewbox.width, viewbox.height)))
        mask_element.add(self._dwg.rect(
            insert=(viewbox.x1, viewbox.y1),
            size=(viewbox.width, viewbox.height),
            fill='rgb({0},{0},{0})'.format(layer.mask.background_color)))
        mask_element.add(self._dwg.image(
            self._get_image_href(layer.mask.as_PIL()),
            size=(layer.mask.width, layer.mask.height),
            insert=(layer.mask.left, layer.mask.top)))
        mask_element['color-interpolation'] = 'sRGB'
        return mask_element

    def create_clipping(self, layer, clip_element):
        """Create clipped elements."""
        # Create a mask for this clip element.
        mask = self._dwg.defs.add(self._dwg.mask())
        use = self._dwg.use(clip_element.get_iri())
        use['filter'] = self._get_white_filter().get_funciri()
        mask.add(use)
        mask['color-interpolation'] = 'sRGB'
        # Group and apply the mask.
        element = self._dwg.g(mask=mask.get_funciri())
        element['class'] = 'psd-clipping'
        for child_layer in reversed(layer.clip_layers):
            clipped_element = self.convert_layer(child_layer)
            if clipped_element:
                element.add(clipped_element)
        return element

    def create_preview(self, hidden=True):
        """Create a preview image of the photoshop."""
        element = self._dwg.image(
            self._get_image_href(self._psd.as_PIL()),
            insert=(0, 0),
            size=(self.width, self.height))
        element['class'] = 'photoshop-image'
        if hidden:
            element['visibility'] = 'hidden'
        return element

    def add_attributes(self, layer, element):
        """Add layer attributes such as blending or visibility options."""
        element.set_desc(title=safe_utf8(layer.name))
        element['class'] = 'psd-layer psd-{}'.format(layer.kind)
        if not layer.visible:
            element['visibility'] = 'hidden'
        blend_mode = BLEND_MODE.get(layer.blend_mode, 'normal')
        if not blend_mode == 'normal':
            element['style'] = 'mix-blend-mode: {}'.format(blend_mode)
        if layer.opacity < 255.0:
            element['opacity'] = layer.opacity / 255.0
        return element

    def add_effects(self, layer, element):
        """Add effects to the element."""
        effects = layer.effects
        fill_opacity = layer.get_tag(
            TaggedBlock.BLEND_FILL_OPACITY, 255) / 255.0
        if not effects:
            if fill_opacity < 1.0:
                element['opacity'] = layer.opacity / 255.0 * fill_opacity
            return element

        interior_blend_mode = None
        if layer.get_tag(TaggedBlock.BLEND_INTERIOR_ELEMENTS, False):
            interior_blend_mode = BLEND_MODE.get(layer.blend_mode, 'normal')
        return self._add_effects(layer.effects, layer, element, fill_opacity,
                                 interior_blend_mode)
