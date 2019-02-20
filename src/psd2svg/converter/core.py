# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
import svgwrite
from psd_tools.api.layers import AdjustmentLayer, FillLayer, ShapeLayer
from psd_tools.api.pil_io import convert_pattern_to_pil
from psd_tools.constants import TaggedBlockID, DescriptorClassID
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

        elif layer.has_pixels():
            element = self.create_image(layer)

        elif isinstance(layer, FillLayer):
            element = self.create_fill(layer)

        elif isinstance(layer, ShapeLayer):
            element = self.create_path(layer)
            element = self.add_fill(layer, element)
            element = self.add_stroke_style(layer, element)

        elif isinstance(layer, AdjustmentLayer):
            return None
            # TODO: Wrap previous elements with the adjustment.
            # element = self.create_adjustment(layer)
        else:
            # Empty layer.
            logger.info('Skipping %s' % layer)
            return None

        element = self.add_attributes(layer, element)
        if layer.has_mask() and not layer.mask.disabled:
            mask_element = self.create_mask(layer)
            if mask_element:
                element['mask'] = mask_element.get_funciri()

        if layer.has_vector_mask() and layer.kind != 'shape':
            clippath = self._dwg.defs.add(self._dwg.clipPath())
            clippath.add(self.create_path(layer))
            element['clip-path'] = clippath.get_funciri()

        element = self.add_effects(layer, element)

        # Clipping is in group, because the parent is not accessible...
        return element

    def create_group(self, group, container=None):
        """Create and fill in a new group element."""
        if not container:
            container = self._dwg.g()
        for layer in group:
            element = self.convert_layer(layer)
            if not element:
                continue
            container.add(element)

            # Clipping layers are in the separate element.
            if layer.clip_layers:
                container.add(self.create_clipping(layer, element))

        return container

    def create_image(self, layer):
        """Create an image element."""
        element = self._dwg.image(
            self._get_image_href(layer.topil()),
            insert=(layer.left, layer.top),
            size=(layer.width, layer.height),
            debug=False)  # To disable attribute validation.
        return element

    def create_path(self, layer):
        """Create a path element."""
        path = self._dwg.path(d=self.generate_path(layer.vector_mask))
        if layer.vector_mask.initial_fill_rule:
            element = self._dwg.defs.add(self._dwg.rect(
                insert=(self._psd.bbox[0], self._psd.bbox[1]),
                size=(self._psd.bbox[2] - self._psd.bbox[0],
                      self._psd.bbox[3] - self._psd.bbox[1])))
            mask = self._dwg.defs.add(self._dwg.mask())
            mask.add(self._dwg.rect(
                insert=(self._psd.bbox[0], self._psd.bbox[1]),
                size=(self._psd.bbox[2] - self._psd.bbox[0],
                      self._psd.bbox[3] - self._psd.bbox[1]),
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
        if layer.bbox != (0, 0, 0, 0):
            element = self._dwg.rect(
                insert=(layer.left, layer.top),
                size=(layer.width, layer.height))
        else:
            element = self._dwg.rect(
                insert=(self._psd.header[0], self._psd.header[1]),
                size=(self._psd.bbox[2] - self._psd.bbox[0],
                      self._psd.bbox[3] - self._psd.bbox[1]))
        element['fill'] = 'none'
        return element

    def create_mask(self, layer):
        """Create a mask."""
        if (
            not layer.has_mask() or
            layer.mask.width == 0 or layer.mask.height == 0
        ):
            return None

        # In SVG, mask needs a default rect.
        viewbox = layer.bbox
        if viewbox == (0, 0, 0, 0):
            viewbox = (0, 0, self.width, self.height)
        mask_element = self._dwg.defs.add(self._dwg.mask(
            size=(viewbox[2] - viewbox[0], viewbox[3] - viewbox[1])))
        mask_element.add(self._dwg.rect(
            insert=(viewbox[0], viewbox[1]),
            size=(viewbox[2] - viewbox[0], viewbox[3] - viewbox[1]),
            fill='rgb({0},{0},{0})'.format(layer.mask.background_color)))
        mask_element.add(self._dwg.image(
            self._get_image_href(layer.mask.topil()),
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
        for child_layer in layer.clip_layers:
            clipped_element = self.convert_layer(child_layer)
            if clipped_element:
                element.add(clipped_element)
        return element

    def create_fill(self, layer):
        element = self.create_rect(layer)
        self.add_fill(layer, element)
        return element

    def add_fill(self, layer, element):
        """Add fill attribute to the given element."""
        if 'SOLID_COLOR_SHEET_SETTING' in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data(
                'SOLID_COLOR_SHEET_SETTING'
            )
            element['fill'] = self.create_solid_color(setting['Clr '])
        elif 'PATTERN_FILL_SETTING' in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data('PATTERN_FILL_SETTING')
            pattern_element = self.create_pattern(setting)
            element['fill'] = pattern_element.get_funciri()
        elif 'GRADIENT_FILL_SETTING' in layer.tagged_blocks:
            setting = layer.tagged_blocks.get_data('GRADIENT_FILL_SETTING')
            gradient = self.create_gradient(setting, layer.size)
            element['fill'] = gradient.get_funciri()
        return element

    def add_attributes(self, layer, element):
        """Add layer attributes such as blending or visibility options."""
        element.set_desc(title=safe_utf8(layer.name))
        element['class'] = 'psd-layer {}'.format(layer.kind)
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

    def create_solid_color(self, color):
        """
        Create a fill attribute.

        This is supposed to be solidColor of SVG 1.2 Tiny spec, but for now,
        implement as fill attribute.

        :rtype: str
        """
        if color.classID == DescriptorClassID(b'RGBC'):
            return 'rgb(%d,%d,%d)' % tuple(map(int, color.values()))
        elif color.classID == DescriptorClassID(b'Grsc'):
            return 'rgb({0},{0},{0})'.format(
                [int(255 * x) for x in color.values()][0]
            )
        elif color.classID == DescriptorClassID(b'CMYC'):
            return 'rgb(%d,%d,%d)' % tuple(*map(int, cmyk2rgb(color.values)))
        else:
            logger.warning('Unsupported color: {}'.format(color))
            return 'rgba(0,0,0,0)'

    def create_pattern(self, setting, insert=(0, 0)):
        """Create a pattern element."""
        pattern_id = setting['Ptrn']['Idnt'].value.strip('\x00')
        pattern = self._psd._get_pattern(pattern_id)
        phase = (0, 0)  #setting.phase
        scale = 100.  #setting.scale.value  # TODO: Check unit
        if not pattern:
            logger.error('Pattern data not found')
            return self._dwg.defs.add(svgwrite.pattern.Pattern())

        image = convert_pattern_to_pil(pattern, self._psd.version)
        element = self._dwg.defs.add(svgwrite.pattern.Pattern(
            width=image.width,
            height=image.height,
            patternUnits='userSpaceOnUse',
            patternContentUnits='userSpaceOnUse',
            patternTransform='translate({},{}) scale({})'.format(
                insert[0] + phase[0], insert[1] + phase[1], scale / 100.0),
        ))
        element.add(self._dwg.image(
            self._get_image_href(image),
            insert=(0, 0),
            size=(image.width, image.height),
        ))
        return element

    def create_gradient(self, setting, size):
        if setting['Type'].enum.value == b'Lnr ':
            theta = np.radians(-setting['Angl'].value)
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
        elif setting['Type'].enum.value == b'Rdl ':
            element = self._dwg.defs.add(svgwrite.gradients.RadialGradient(
                center=None, r=.5))
        else:
            logger.warning('Unsupported gradient type %s' % (setting['Type']))
            return None

        gradient = setting.get('Grad')
        if not gradient.get('Clrs'):
            logger.warning("Unsupported gradient type %s".format(gradient))
            return element

        # Interpolate color and opacity for both points.
        cp = np.array([x['Lctn'].value / 4096.0 for x in gradient['Clrs']])
        op = np.array([x['Lctn'].value / 4096.0 for x in gradient['Trns']])
        c_items = np.array([
            tuple(z.value for z in x['Clr '].values())
            for x in gradient['Clrs']
        ]).transpose()
        o_items = np.array([x['Opct'].value / 100.0
                            for x in gradient['Trns']])  # TODO: Check unit.

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
        if setting.get('Rvrs'):
            cp = 1.0 - cp[::-1]
            op = 1.0 - op[::-1]
            c_items = c_items[:, ::-1]
            o_items = o_items[::-1]

        mp = np.unique(np.concatenate((cp, op)))
        fc = np.stack([
            np.interp(mp, cp, c_items[index, :])
            for index in range(3)
        ])
        fo = np.interp(mp, op, o_items)

        for index in range(len(mp)):
            color = tuple(fc[:, index].astype(np.uint8).tolist())
            element.add_stop_color(offset=mp[index], opacity=fo[index],
                                   color='rgb{}'.format(color))
        return element
