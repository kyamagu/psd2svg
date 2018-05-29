# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
import svgwrite
from psd_tools.user_api import BBox
from psd_tools.constants import TaggedBlock
from psd2svg.converter.constants import BLEND_MODE
from psd2svg.utils.xml import safe_utf8
from psd2svg.utils.color import cmyk2rgb
import numpy as np

logger = getLogger(__name__)


class LayerConverter(object):

    def convert_layer(self, layer):
        """
        Convert the given layer.

        The current implementation always converts a PSD layer to a single
        SVG element.

        :return: SVG element.
        """
        if layer.is_group():
            element = self.create_group(layer)

        elif layer.has_relevant_pixels():
            element = self.create_image(layer)
            if layer.kind == 'type':
                # TODO: Embed text metadata.
                # text = self._get_text(layer)
                pass

        elif layer.kind == 'shape' and layer.has_path():
            element = self.create_path(layer)
            # TODO: Deal with coflict in add_attributes() later.
            # Blending, mask, and class names conflict.
            element = self.add_stroke_style(layer, element)
            element = self.add_stroke_content_style(layer, element)

        elif layer.kind == 'adjustment':
            element = self.create_adjustment(layer)
            # TODO: Wrap previous elements with the adjustment.

        else:
            # Boxless shape fill.
            element = self.create_rect(layer)

        element = self.add_fill(layer, element)
        element = self.add_attributes(layer, element)
        if layer.has_mask():
            mask = layer.mask
            if mask.has_box() and not mask.disabled and (
                    not mask.user_mask_from_render):
                mask_element = self.create_mask(layer)
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
        """Create an image element."""
        element = self._dwg.image(
            self._get_image_href(layer.as_PIL()),
            insert=(layer.left, layer.top),
            size=(layer.width, layer.height),
            debug=False)  # To disable attribute validation.
        return element

    def create_path(self, layer):
        """Create a path element."""
        path = self._dwg.path(d=self.generate_path(layer.vector_mask))
        if layer.vector_mask.initial_fill_rule:
            element = self._dwg.defs.add(self._dwg.rect(
                insert=(self._psd.bbox.x1, self._psd.bbox.y1),
                size=(self._psd.bbox.width, self._psd.bbox.height)))
            mask = self._dwg.defs.add(self._dwg.mask())
            mask.add(self._dwg.rect(
                insert=(self._psd.bbox.x1, self._psd.bbox.y1),
                size=(self._psd.bbox.width, self._psd.bbox.height),
                fill='white'))
            path['fill'] = 'black'
            path['clip-rule'] = 'evenodd'
            mask.add(path)
            element['mask'] = mask.get_funciri()
            use = self._dwg.use(element.get_iri())
            return use
        else:
            path['fill-rule'] = 'evenodd'
            return path

    def create_rect(self, layer):
        """Create a shape or adjustment element."""
        if layer.has_box():
            element = self._dwg.rect(
                insert=(layer.left, layer.top),
                size=(layer.width, layer.height))
        else:
            element = self._dwg.rect(
                insert=(self._psd.bbox.x1, self._psd.bbox.y1),
                size=(self._psd.bbox.width, self._psd.bbox.height))
        element['fill'] = 'none'
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
        if isinstance(clip_element, svgwrite.path.Path):
            clippath = self._dwg.defs.add(self._dwg.clipPath())
            use = self._dwg.use(clip_element.get_iri())
            clippath.add(use)
            element = self._dwg.g()
            element['clip-path'] = clippath.get_funciri()
        else:
            mask = self._dwg.defs.add(self._dwg.mask())
            use = self._dwg.use(clip_element.get_iri())
            use['filter'] = self._get_white_filter().get_funciri()
            mask.add(use)
            mask['color-interpolation'] = 'sRGB'
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

    def add_fill(self, layer, element):
        """Add fill attribute to the given element."""
        if layer.has_tag(TaggedBlock.SOLID_COLOR_SHEET_SETTING):
            effect = layer.get_tag(TaggedBlock.SOLID_COLOR_SHEET_SETTING)
            element['fill'] = self.create_solid_color(effect)
        elif layer.has_tag(TaggedBlock.PATTERN_FILL_SETTING):
            effect = layer.get_tag(TaggedBlock.PATTERN_FILL_SETTING)
            pattern_element = self.create_pattern(effect)
            element['fill'] = pattern_element.get_funciri()
        elif layer.has_tag(TaggedBlock.GRADIENT_FILL_SETTING):
            effect = layer.get_tag(TaggedBlock.GRADIENT_FILL_SETTING)
            if layer.kind == 'shape' and not layer.has_box():
                bbox = layer.get_bbox(vector=True)
            else:
                bbox = layer.bbox
            if bbox.is_empty():
                bbox = layer._psd.viewbox
            gradient = self.create_gradient(effect, (bbox.width, bbox.height))
            element['fill'] = gradient.get_funciri()
        return element

    def add_attributes(self, layer, element):
        """Add layer attributes such as blending or visibility options."""
        element.set_desc(title=safe_utf8(layer.name))
        element['class'] = 'psd-layer psd-{}'.format(layer.kind)
        if not layer.visible:
            element['visibility'] = 'hidden'
        if layer.opacity < 255.0:
            element['opacity'] = layer.opacity / 255.0
        self.add_blend_mode(element, layer.blend_mode)
        return element

    def add_blend_mode(self, element, blend_mode):
        """Set blending option to the element."""
        blend_mode = BLEND_MODE.get(blend_mode, 'normal')
        if blend_mode != 'normal':
            if 'style' in element.attribs:
                element['style'] += 'mix-blend-mode: {};'.format(blend_mode)
            else:
                element['style'] = 'mix-blend-mode: {};'.format(blend_mode)

    def create_solid_color(self, effect):
        """
        Create a fill attribute.

        This is supposed to be solidColor of SVG 1.2 Tiny spec, but for now,
        implement as fill attribute.

        :rtype: str
        """
        if hasattr(effect, 'color'):
            color = effect.color
        else:
            color = effect
        if color.name == 'rgb':
            return 'rgb({},{},{})'.format(*map(int, color.value))
        elif color.name == 'gray':
            return 'rgb({0},{0},{0})'.format(int(255 * color.value[0]))
        elif color.name == 'cmyk':
            rgb = cmyk2rgb(color.value)
            return 'rgb({},{},{})'.format(*map(int, rgb))
        else:
            logger.warning('Unsupported color: {}'.format(color))
            return 'rgba(0,0,0,0)'

    def create_pattern(self, effect, insert=(0, 0)):
        """Create a pattern element."""
        pattern = self._psd.patterns.get(effect.pattern.id)
        phase = effect.phase
        scale = effect.scale.value  # TODO: Check unit
        if not pattern:
            logger.error('Pattern data not found')
            return self._dwg.defs.add(svgwrite.pattern.Pattern())

        element = self._dwg.defs.add(svgwrite.pattern.Pattern(
            width=pattern.width,
            height=pattern.height,
            patternUnits='userSpaceOnUse',
            patternContentUnits='userSpaceOnUse',
            patternTransform='translate({},{}) scale({})'.format(
                insert[0] + phase[0], insert[1] + phase[1], scale / 100.0),
        ))
        element.add(self._dwg.image(
            self._get_image_href(pattern.as_PIL()),
            insert=(0, 0),
            size=(pattern.width, pattern.height),
        ))
        return element

    def create_gradient(self, effect, size):
        if effect.type == 'radial':
            element = self._dwg.defs.add(svgwrite.gradients.RadialGradient(
                center=None, r=.5))
        else:
            theta = np.radians(-effect.angle.value)
            start = np.array([size[0] * np.cos(theta - np.pi),
                              size[1] * np.sin(theta - np.pi)])
            end = np.array([size[0] * np.cos(theta), size[1] * np.sin(theta)])
            r = 1.0 * np.max(np.abs(start))

            start = start / (2.0 * r) + 0.5
            end = end / (2.0 * r) + 0.5

            start = [np.around(x, decimals=6) for x in start]
            end = [np.around(x, decimals=6) for x in end]

            element = self._dwg.defs.add(svgwrite.gradients.LinearGradient(
                start=start, end=end))

        gradient = effect.gradient
        if not gradient.colors:
            logger.warning("Unsupported gradient type: {}".format(gradient))
            return element

        # Interpolate color and opacity for both points.
        cp = np.array([x.location / 4096.0 for x in gradient.colors])
        op = np.array([x.location / 4096.0 for x in gradient.transform])
        c_items = np.array([
            x.color.value for x in gradient.colors]).transpose()
        o_items = np.array([x.opacity.value / 100.0
                            for x in gradient.transform])  # TODO: Check unit.

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
        if effect.reversed:
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
            element.add_stop_color(offset=mp[index], opacity=fo[index],
                                   color='rgb{}'.format(color))
        return element
