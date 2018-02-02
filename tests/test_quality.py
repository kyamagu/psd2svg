from __future__ import absolute_import, unicode_literals

import unittest
from glob import glob
import os
import pytest
import imagehash
import psd2svg
import psd2svg.rasterizer
from psd_tools import PSDImage
from pprint import pprint

FIXTURES = [
    p for p in glob(
        os.path.join(os.path.dirname(__file__), 'fixtures', '*.psd'))
]

HARD_CASES = [
    os.path.join(os.path.dirname(__file__), 'fixtures', p) for p in [
        "layer_effects.psd",
        "layer_params.psd",
        "layer_comps.psd",
        "gray0.psd",  # Seems the preview image is inaccurate.
    ]
]

EASY_CASES = list(set(FIXTURES) - set(HARD_CASES))


@pytest.fixture(scope="module")
def rasterizer():
    return psd2svg.rasterizer.create_rasterizer()


@pytest.mark.parametrize('psd_file', EASY_CASES)
def test_quality(rasterizer, tmpdir, psd_file):
    svg_file = os.path.join(tmpdir.dirname, "output.svg")
    psd = PSDImage.load(psd_file)
    preview = psd.as_PIL().convert("RGBA")
    psd2svg.psd2svg(psd, svg_file, no_preview=True)
    rendered = rasterizer.rasterize(svg_file)
    assert preview.width == rendered.width
    assert preview.height == rendered.height
    preview_hash = imagehash.average_hash(preview)
    rendered_hash = imagehash.average_hash(rendered)
    assert(preview_hash == rendered_hash)
