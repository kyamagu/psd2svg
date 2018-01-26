from __future__ import absolute_import, unicode_literals

import unittest
from glob import glob
import os
import pytest
import imagehash
import psd2svg
import psd2svg.rasterizer
from psd_tools import PSDImage

FIXTURES = [
    p for p in glob(
        os.path.join(os.path.dirname(__file__), 'fixtures', '*.psd'))
    ]


@pytest.fixture(scope="module")
def rasterizer():
    return psd2svg.rasterizer.create_rasterizer()


@pytest.mark.parametrize('psd_file', FIXTURES)
def test_quality(rasterizer, tmpdir, psd_file):
    svg_file = os.path.join(tmpdir.dirname, "output.svg")
    psd = PSDImage.load(psd_file)
    preview = psd.as_PIL()
    psd2svg.psd2svg(psd, svg_file)
    rendered = rasterizer.rasterize(svg_file)
    assert preview.width == rendered.width
    assert preview.height == rendered.height
    preview_hash = imagehash.average_hash(preview)
    rendered_hash = imagehash.average_hash(preview)
    assert(preview_hash == rendered_hash)
