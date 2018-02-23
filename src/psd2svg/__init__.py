# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger
import svgwrite
from psd2svg.converter.adjustments import AdjustmentsConverter
from psd2svg.converter.core import LayerConverter
from psd2svg.converter.effects import EffectsConverter
from psd2svg.converter.io import PSDReader, SVGWriter
from psd2svg.converter.shape import ShapeConverter
from psd2svg.converter.text import TextConverter
from psd2svg.version import __version__


logger = getLogger(__name__)


def psd2svg(input, output=None, **kwargs):
    converter = PSD2SVG(**kwargs)
    return converter.convert(input, output)


class PSD2SVG(AdjustmentsConverter, EffectsConverter, LayerConverter,
              PSDReader, ShapeConverter, SVGWriter, TextConverter):
    """PSD to SVG converter

    input_url - url, file-like object, PSDImage, or any of its layer.
    output_url - url or file-like object to export svg. if None, return data.
    text_mode - option to switch text rendering (default 'image')
      * 'image' use Photoshop's bitmap
      * 'text' use SVG text
      * 'image-only' use Photoshop's bitmap and discard SVG text
      * 'text-only' use SVG text and discard Photoshop bitmap
    export_resource - use dataURI to embed bitmap (default True)
    """
    def __init__(self, text_mode='image', export_resource=False,
                 resource_prefix='', overwrite=True, reset_id=True,
                 no_preview=False):
        self.text_mode = text_mode
        self.export_resource = export_resource
        self.resource_prefix = resource_prefix
        self.overwrite = overwrite
        self.reset_id = reset_id
        self.no_preview = no_preview

    def reset(self):
        """Reset the converter."""
        self._psd = None
        self._input_layer = None
        self._white_filter = None
        self._identity_filter = None
        if self.reset_id:
            svgwrite.utils.AutoID._set_value(0)

    def convert(self, input, output=None, layer_view=True):
        """Convert the given PSD to SVG."""
        self.reset()
        self._load(input)
        self._set_output(output)

        if (not self.overwrite and self._output_file and
                self._output.exists(self._output_file)):
            url = self._output.url(self._output_file)
            logger.warning('File exists: {}'.format(url))
            return url

        if layer_view and self._input_layer and self._input_layer.has_box():
            self._dwg = svgwrite.Drawing(
                size=(self._input_layer.width, self._input_layer.height),
                viewBox="{} {} {} {}".format(
                    self._input_layer.left, self._input_layer.top,
                    self._input_layer.width, self._input_layer.height))
        else:
            self._dwg = svgwrite.Drawing(
                size=(self.width, self.height),
                viewBox="0 0 {} {}".format(self.width, self.height))

        # if self.text_mode in ('image', 'image-only'):
        #     stylesheet = '.text-text { display: none; }'
        # elif self.text_mode in ('text', 'text-only'):
        #     stylesheet = '.text-image { display: none; }'
        # self._dwg.defs.add(self._dwg.style(stylesheet))

        # Add layers.
        if self._input_layer:
            self._dwg.add(self.convert_layer(self._input_layer))
        else:
            self.create_group(self._psd, element=self._dwg)
            empty_psd = len(self._psd.layers) == 0
            if not self.no_preview or empty_psd:
                self._dwg.add(self.create_preview(hidden=not empty_psd))

        return self._save_svg()

    @property
    def width(self):
        return self._psd.width if hasattr(self, '_psd') else None

    @property
    def height(self):
        return self._psd.height if hasattr(self, '_psd') else None
