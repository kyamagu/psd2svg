import logging
import os

import pytest
from psd_tools import PSDImage

from psd2svg import convert
from psd2svg.eval import compute_conversion_quality

from .conftest import get_fixture


@pytest.mark.parametrize(
    "psd_file",
    [
        "layer-types/black-and-white.psd",
        "layer-types/brightness-contrast.psd",
        "layer-types/channel-mixer.psd",
        "layer-types/color-balance.psd",
        "layer-types/curves-with-vectormask.psd",
        "layer-types/curves.psd",
        "layer-types/exposure.psd",
        "layer-types/gradient-map-v3-classic.psd",
        "layer-types/gradient-map-v3-linear.psd",
        "layer-types/gradient-map.psd",
        "layer-types/hue-saturation.psd",
        "layer-types/invert.psd",
        "layer-types/levels.psd",
        "layer-types/photo-filter.psd",
        "layer-types/selective-color.psd",
        "layer-types/threshold.psd",
        "layer-types/vibrance.psd",
        "layer-types/gradient-fill.psd",
        "layer-types/solid-color-fill.psd",
        "layer-types/pattern-fill.psd",
        "layer-types/artboard.psd",
        "layer-types/group.psd",
        "layer-types/pixel-layer.psd",
        "layer-types/shape-layer.psd",
        "layer-types/smartobject-layer.psd",
        "layer-types/type-layer.psd",
    ],
)
def test_convert(tmpdir, psd_file: str) -> None:
    """Test conversion succeeds for various file types."""
    input_path = get_fixture(psd_file)
    output_path = tmpdir.dirname + "/output.svg"
    images_path = tmpdir.dirname + "/images"
    convert(input_path, output_path, images_path)
    assert os.path.exists(output_path)


def evaluate_quality(psd_file: str, quality: float) -> None:
    """Generic quality evaluation helper."""
    psdimage = PSDImage.open(get_fixture(psd_file))
    score = compute_conversion_quality(psdimage, "MSE")
    logging.info(f"MSE for {psd_file}: {score} vs. {quality}")
    assert score < quality, f"MSE is too high: {score} vs. {quality}"


@pytest.mark.parametrize(
    "psd_file, quality",
    [
        pytest.param("layer-types/artboard.psd", 0.01),
        pytest.param("layer-types/group.psd", 0.01),
        pytest.param("layer-types/pixel-layer.psd", 0.01),
        pytest.param(
            "layer-types/shape-layer.psd", 0.02
        ),  # Shape layers may require a bit more tolerance
        pytest.param("layer-types/smartobject-layer.psd", 0.01),
        pytest.param("layer-types/type-layer.psd", 0.01),
        pytest.param("layer-types/gradient-fill.psd", 0.01),
        pytest.param("layer-types/solid-color-fill.psd", 0.01),
        pytest.param("layer-types/pattern-fill.psd", 0.01),
    ],
)
def test_layer_types_quality(psd_file: str, quality: float) -> None:
    """Test conversion quality for various layer types."""
    evaluate_quality(psd_file, quality)


@pytest.mark.parametrize(
    "psd_file, quality",
    [
        pytest.param(
            "clipping/group-with-clip-stroke-effect.psd",
            0.02,
            marks=pytest.mark.xfail(reason="Stroke effect is inaccurate."),
        ),
        pytest.param("clipping/group-with-clip-stroke.psd", 0.02),
        pytest.param("clipping/pixel-with-clip-stroke-effect.psd", 0.02),
        pytest.param("clipping/shape-with-clip-stroke-effect.psd", 0.02),
        pytest.param("clipping/shape-with-clip-stroke.psd", 0.02),
        pytest.param("clipping/shape-with-clip2-stroke.psd", 0.02),
        pytest.param("clipping/shape-with-invisible-clip.psd", 0.01),
        pytest.param(
            "clipping/shape-with-blend.psd", 0.01
        ),  # Blend mode for clipping shape layer
        pytest.param(
            "clipping/pixel-with-blend.psd", 0.01
        ),  # Blend mode for clipping pixel layer
    ],
)
def test_clipping(psd_file: str, quality: float) -> None:
    """Test converting PSD files with clipping masks to SVG."""
    evaluate_quality(psd_file, quality)


@pytest.mark.parametrize(
    "psd_file",
    [
        "shapes/triangle-1.psd",
        "shapes/triangle-2.psd",
        "shapes/custom-1.psd",  # Complex custom shape with a subpath
        "shapes/custom-2.psd",  # Complex custom shape with a subpath and a mask
        "shapes/custom-3.psd",  # Complex custom shape with composite subpaths
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
        "shapes/multi-1.psd",  # Union + Subtract
        "shapes/multi-2.psd",  # Union + Subtract + Intersect
        "shapes/multi-3.psd",  # Union + Subtract + Union
        "shapes/multi-4.psd",  # Union + XOR with composite subpaths, this one requires 0.02 threshold
    ],
)
def test_shapes(psd_file: str) -> None:
    """Test conversion quality of shape layers."""
    evaluate_quality(psd_file, 0.02)


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
    evaluate_quality(psd_file, 0.01)


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
        "effects/color-overlay-5.psd",  # transparent fill opacity test
        "effects/color-overlay-6.psd",  # raster fill opacity and mask test
        "effects/color-overlay-7.psd",  # vector fill opacity and mask test
        "effects/gradient-overlay-1.psd",
        "effects/gradient-overlay-2.psd",
        "effects/gradient-overlay-3.psd",
        "effects/gradient-overlay-4.psd",
        "effects/gradient-overlay-5.psd",
        "effects/gradient-overlay-6.psd",  # fill layer with overlay effect
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
    evaluate_quality(psd_file, 0.01)


@pytest.mark.parametrize(
    "psd_file",
    [
        "layer-types/gradient-fill.psd",
        "layer-types/pattern-fill.psd",
        "layer-types/solid-color-fill.psd",
    ],
)
def test_fill_layers(psd_file: str) -> None:
    """Test conversion quality of fill layers."""
    evaluate_quality(psd_file, 0.01)
