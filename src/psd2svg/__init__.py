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


def psd2svg(input_url, output_url='', **kwargs):
    converter = PSD2SVG(**kwargs)
    converter.load(input_url)
    return converter.convert(output_url)


class PSD2SVG(AdjustmentsConverter, EffectsConverter, LayerConverter,
              PSDReader, ShapeConverter, SVGWriter, TextConverter):
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

    def load(self, url):
        self._load(url)

    def load_stream(self, stream):
        self._load_stream(stream)

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
        self._add_photoshop_view()

        return self._save_svg()

    @property
    def width(self):
        return self._psd.header.width if self._psd else None

    @property
    def height(self):
        return self._psd.header.height if self._psd else None
