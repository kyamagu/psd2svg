import logging
import os

import psd_tools
import pytest

from psd2svg import Converter
from psd2svg.eval import compute_conversion_quality

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
def test_quality(psd_file: str) -> None:
    """Test conversion quality in the raster format."""
    psdimage = psd_tools.PSDImage.open(get_fixture(psd_file))
    score = compute_conversion_quality(psdimage, "MSE")
    logging.info(f"MSE for {psd_file}: {score}")
    assert score < 0.05, f"MSE is too high: {score}"


@pytest.mark.parametrize(
    "psd_file, quality",
    [
        pytest.param(
            "clipping/group-with-clip-stroke-effect.psd",
            0.02,
            marks=pytest.mark.xfail(reason="Stroke effect is inaccurate."),
        ),
        pytest.param("clipping/group-with-clip-stroke.psd", 0.02),
        pytest.param(
            "clipping/pixel-with-clip-stroke-effect.psd",
            0.02,
            marks=pytest.mark.xfail(reason="Stroke effect is inaccurate."),
        ),
        pytest.param("clipping/shape-with-clip-stroke-effect.psd", 0.02),
        pytest.param("clipping/shape-with-clip-stroke.psd", 0.02),
        pytest.param("clipping/shape-with-clip2-stroke.psd", 0.02),
    ],
)
def test_clipping(psd_file: str, quality: float) -> None:
    """Test converting PSD files with clipping masks to SVG."""
    psdimage = psd_tools.PSDImage.open(get_fixture(psd_file))
    score = compute_conversion_quality(psdimage, "MSE")
    logging.info(f"MSE for {psd_file}: {score} vs. {quality}")
    assert score < quality, f"MSE is too high: {score} vs. {quality}"
