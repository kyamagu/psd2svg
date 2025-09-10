import pytest
import os

import imagehash
import numpy as np
import psd_tools
from psd2svg import Converter
from psd2svg.rasterizer.resvg_rasterizer import ResvgRasterizer

from .conftest import ALL, TYPES, get_fixture


@pytest.mark.parametrize("psd_file", ALL)
def test_convert(tmpdir, psd_file: str) -> None:
    """Test converting PSD files to SVG."""

    input_path = get_fixture(psd_file)
    output_path = tmpdir.dirname + "/output.svg"
    images_path = tmpdir.dirname + "/images"
    Converter.convert(input_path, output_path, images_path)
    assert os.path.exists(output_path)


@pytest.mark.parametrize("psd_file", TYPES)
def test_quality(tmpdir, psd_file: str) -> None:
    """Test conversion quality in the raster format."""

    input_path = get_fixture(psd_file)
    svg_path = tmpdir.dirname + "/output.svg"
    images_path = tmpdir.dirname + "/images"
    rasterizer = ResvgRasterizer()

    # Convert PSD to SVG.
    Converter.convert(input_path, svg_path, images_path)
    assert os.path.exists(svg_path)

    # Rasterize SVG and compare with original PSD.
    rasterized = rasterizer.rasterize(svg_path)
    original = psd_tools.PSDImage.open(input_path).composite()

    # Quality check.
    assert rasterized.width == original.width
    assert rasterized.height == original.height
    input_hash = imagehash.phash(original)
    output_hash = imagehash.phash(rasterized)
    error_rate = np.sum(np.bitwise_xor(input_hash.hash, output_hash.hash)) / float(
        input_hash.hash.size
    )
    assert error_rate <= 0.125
