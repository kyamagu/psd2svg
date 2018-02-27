from __future__ import absolute_import, unicode_literals

from glob import glob
import os
import pytest
import imagehash
import numpy as np
import psd2svg
import psd2svg.rasterizer
from psd_tools import PSDImage

FIXTURES = [
    p for p in glob(
        os.path.join(os.path.dirname(__file__), 'fixtures', '*.psd'))
]

HARD_CASES = [
    os.path.join(os.path.dirname(__file__), 'fixtures', p) for p in [
        "advanced-blending.psd",
        "layer_params.psd",
        "gray0.psd",  # Seems the preview image is inaccurate.
    ]
]

EASY_CASES = list(set(FIXTURES) - set(HARD_CASES))


@pytest.fixture(scope="module")
def rasterizer():
    rasterizer = psd2svg.rasterizer.create_rasterizer()
    yield rasterizer
    del rasterizer


@pytest.mark.parametrize('psd_file', EASY_CASES)
def test_quality(rasterizer, tmpdir, psd_file):
    svg_file = os.path.join(tmpdir.dirname, "output.svg")
    psd = PSDImage.load(psd_file)
    if not psd.has_preview():
        pytest.skip('psd file does not have a preview, skipping tests')
    preview = psd.as_PIL()
    psd2svg.psd2svg(psd, svg_file, no_preview=True)
    rendered = rasterizer.rasterize(svg_file)
    assert preview.width == rendered.width
    assert preview.height == rendered.height
    preview_hash = imagehash.average_hash(preview)
    rendered_hash = imagehash.average_hash(rendered)
    error_count = np.sum(
        np.bitwise_xor(preview_hash.hash, rendered_hash.hash))
    error_rate = error_count / float(preview_hash.hash.size)
    assert error_rate <= 0.1
