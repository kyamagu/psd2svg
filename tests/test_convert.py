import logging
import os

import numpy as np
import psd_tools
import pytest

from psd2svg import Converter
from psd2svg.rasterizer.resvg_rasterizer import ResvgRasterizer

from .conftest import ALL, TYPES, FILLS, get_fixture


@pytest.mark.parametrize("psd_file", ALL)
def test_convert(tmpdir, psd_file: str) -> None:
    """Test converting PSD files to SVG."""

    input_path = get_fixture(psd_file)
    output_path = tmpdir.dirname + "/output.svg"
    images_path = tmpdir.dirname + "/images"
    Converter.convert(input_path, output_path, images_path)
    assert os.path.exists(output_path)


@pytest.mark.parametrize("psd_file", TYPES + FILLS)
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
    if original.mode != "RGBA":
        original = original.convert("RGBA")

    # Quality check.
    assert rasterized.width == original.width
    assert rasterized.height == original.height
    assert rasterized.mode == original.mode

    rasterized_array = np.array(rasterized, dtype=np.float32) / 255.0
    original_array = np.array(original, dtype=np.float32) / 255.0
    mae = np.nanmean(np.abs(rasterized_array - original_array))
    logging.info(f"MAE for {psd_file}: {mae}")
    assert mae < 0.05, f"MAE is too high: {mae}"