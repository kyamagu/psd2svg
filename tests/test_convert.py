import logging
import os

import pytest
from psd_tools import PSDImage

from psd2svg import convert
from psd2svg.eval import compute_conversion_quality

from .conftest import ALL, TYPES, FILLS, get_fixture


@pytest.mark.parametrize("psd_file", ALL)
def test_convert(tmpdir, psd_file: str) -> None:
    """Test converting PSD files to SVG."""

    input_path = get_fixture(psd_file)
    output_path = tmpdir.dirname + "/output.svg"
    images_path = tmpdir.dirname + "/images"
    convert(input_path, output_path, images_path)
    assert os.path.exists(output_path)


@pytest.mark.parametrize("psd_file", TYPES + FILLS)
def test_quality(psd_file: str) -> None:
    """Test conversion quality in the raster format."""
    psdimage = PSDImage.open(get_fixture(psd_file))
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
        pytest.param("clipping/shape-with-invisible-clip.psd", 0.02),
    ],
)
def test_clipping(psd_file: str, quality: float) -> None:
    """Test converting PSD files with clipping masks to SVG."""
    psdimage = PSDImage.open(get_fixture(psd_file))
    score = compute_conversion_quality(psdimage, "MSE")
    logging.info(f"MSE for {psd_file}: {score} vs. {quality}")
    assert score < quality, f"MSE is too high: {score} vs. {quality}"


@pytest.mark.parametrize(
    "psd_file",
    [
        "shapes/triangle-1.psd",
        "shapes/triangle-2.psd",
        "shapes/custom-1.psd",
        "shapes/ellipse-1.psd",
        "shapes/ellipse-2.psd",
        "shapes/ellipse-3.psd",
        "shapes/line-1.psd",
        "shapes/line-2.psd",
        "shapes/polygon-1.psd",
        "shapes/polygon-2.psd",
        "shapes/rectangle-1.psd",
        "shapes/rectangle-2.psd",
        "shapes/rectangle-3.psd",
        "shapes/rectangle-4.psd",
        "shapes/rectangle-5.psd",
        "shapes/star-1.psd",
        "shapes/star-2.psd",
        "shapes/multi-1.psd",
        "shapes/multi-2.psd",
        "shapes/multi-3.psd",
    ],
)
def test_shapes(psd_file: str) -> None:
    """Test conversion quality in the raster format."""
    psdimage = PSDImage.open(get_fixture(psd_file))
    score = compute_conversion_quality(psdimage, "MSE")
    logging.info(f"MSE for {psd_file}: {score}")
    assert score < 0.05, f"MSE is too high: {score}"


@pytest.mark.parametrize(
    "psd_file",
    [
        "paint/transparent-1.psd",
        "paint/color-1.psd",
        "paint/color-2.psd",  # Fill opacity test for shape layer
        "paint/color-3.psd",  # Fill opacity test for raster layer
        "paint/linear-gradient-1.psd",
        "paint/linear-gradient-2.psd",  # Fill opacity test
        "paint/radial-gradient-1.psd",
    ],
)
def test_paint(psd_file: str) -> None:
    """Test conversion quality for painting."""
    psdimage = PSDImage.open(get_fixture(psd_file))
    score = compute_conversion_quality(psdimage, "MSE")
    logging.info(f"MSE for {psd_file}: {score}")
    assert score < 0.05, f"MSE is too high: {score}"


@pytest.mark.parametrize(
    "psd_file",
    [
        "effects/color-overlay-1.psd",
        "effects/color-overlay-2.psd",
        pytest.param(
            "effects/color-overlay-3.psd",
            marks=pytest.mark.xfail(reason="Outset stroke is not supported."),
        ),
        "effects/color-overlay-4.psd",
        "effects/gradient-overlay-1.psd",
        "effects/gradient-overlay-2.psd",
        "effects/gradient-overlay-3.psd",
        "effects/gradient-overlay-4.psd",
        "effects/gradient-overlay-5.psd",
        "effects/pattern-overlay-1.psd",  # raster pattern overlay
        "effects/pattern-overlay-2.psd",  # raster pattern overlay with transform
        "effects/pattern-overlay-3.psd",  # shape pattern overlay
        "effects/pattern-overlay-4.psd",  # shape pattern overlay with transform
        "effects/drop-shadow-1.psd",
        "effects/drop-shadow-2.psd",
        "effects/drop-shadow-3.psd",
        "effects/drop-shadow-4.psd",
        pytest.param(
            "effects/drop-shadow-5.psd",
            marks=pytest.mark.xfail(reason="Morphology filter is limited."),
        ),
        "effects/drop-shadow-6.psd",
        "effects/inner-shadow-1.psd",
        "effects/inner-shadow-2.psd",
        "effects/outer-glow-1.psd",
        "effects/outer-glow-2.psd",
        "effects/inner-glow-1.psd",
        "effects/inner-glow-2.psd",
        "effects/inner-glow-3.psd",
    ],
)
def test_effects(psd_file: str) -> None:
    """Test conversion quality in the raster format."""
    psdimage = PSDImage.open(get_fixture(psd_file))
    score = compute_conversion_quality(psdimage, "MSE")
    logging.info(f"MSE for {psd_file}: {score}")
    assert score < 0.01, f"MSE is too high: {score}"
