from __future__ import absolute_import
from .version import __version__
from .convert import PSD2SVG
from .storage import *


def psd2svg(input_url, output_url='', **kwargs):
    converter = PSD2SVG(**kwargs)
    converter.load(input_url)
    return converter.convert(output_url)
