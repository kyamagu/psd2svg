import logging
import os
from pathlib import Path

import pytest
from psd_tools import PSDImage

from psd2svg import convert
from psd2svg.core.converter import Converter
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
def test_convert(tmp_path: Path, psd_file: str) -> None:
    """Test conversion succeeds for various file types."""
    input_path = get_fixture(psd_file)
    output_path = str(tmp_path / "output.svg")
    images_path = str(tmp_path / "images")
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
        pytest.param(
            "layer-types/type-layer.psd",
            0.01,
            marks=pytest.mark.xfail(
                reason="Text layer support is not fully implemented."
            ),
        ),
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
        # Tests for clipping with transforms.
        pytest.param("clipping/clipping-1-raster-with-transform.psd", 0.005),
        pytest.param("clipping/clipping-1-vector-with-transform.psd", 0.005),
        pytest.param("clipping/clipping-2-raster-with-transform.psd", 0.005),
        pytest.param("clipping/clipping-2-vector-with-transform.psd", 0.005),
        pytest.param("clipping/clipping-3-raster-with-transform.psd", 0.005),
        pytest.param("clipping/clipping-3-vector-with-transform.psd", 0.005),
        # Tests for clipping with masks and transforms.
        pytest.param(
            "clipping/clipping-4-pixel-mask-with-transform-w-mask.psd",
            0.005,
        ),
        pytest.param(
            "clipping/clipping-4-pixel-mask-with-transform-wo-mask.psd",
            0.005,
        ),
        pytest.param(
            "clipping/clipping-4-shape-mask-with-transform-w-mask.psd",
            0.005,
        ),
        pytest.param(
            "clipping/clipping-4-shape-mask-with-transform-wo-mask.psd",
            0.005,
        ),
        pytest.param(
            "clipping/clipping-4-shape-mask-clippath.psd",
            0.005,
        ),
    ],
)
def test_clipping(psd_file: str, quality: float) -> None:
    """Test converting PSD files with clipping masks to SVG."""
    evaluate_quality(psd_file, quality)


@pytest.mark.parametrize(
    "psd_file, quality",
    [
        pytest.param("blend-modes/effect-color-burn.psd", 0.01),
        pytest.param("blend-modes/effect-color-dodge.psd", 0.01),
        pytest.param("blend-modes/effect-color.psd", 0.01),
        pytest.param("blend-modes/effect-darken.psd", 0.01),
        pytest.param("blend-modes/effect-darker-color.psd", 0.01),
        pytest.param("blend-modes/effect-difference.psd", 0.01),
        pytest.param(
            "blend-modes/effect-dissolve.psd", 0.01
        ),  # Dissolve is not supported, but MSE is low.
        pytest.param(
            "blend-modes/effect-divide.psd",
            0.01,
            marks=pytest.mark.xfail(reason="Divide is not accurately supported."),
        ),
        pytest.param("blend-modes/effect-exclusion.psd", 0.01),
        pytest.param("blend-modes/effect-hard-light.psd", 0.01),
        pytest.param(
            "blend-modes/effect-hard-mix.psd",
            0.01,
            marks=pytest.mark.xfail(reason="Hard mix is not accurately supported."),
        ),
        pytest.param("blend-modes/effect-hue.psd", 0.01),
        pytest.param("blend-modes/effect-lighten.psd", 0.01),
        pytest.param("blend-modes/effect-lighter-color.psd", 0.01),
        pytest.param(
            "blend-modes/effect-linear-burn.psd",
            0.01,
            marks=pytest.mark.xfail(reason="Linear burn is not accurately supported."),
        ),
        pytest.param(
            "blend-modes/effect-linear-dodge.psd",
            0.01,
            marks=pytest.mark.xfail(reason="Linear dodge is not accurately supported."),
        ),
        pytest.param(
            "blend-modes/effect-linear-light.psd",
            0.01,
            marks=pytest.mark.xfail(reason="Linear light is not accurately supported."),
        ),
        pytest.param("blend-modes/effect-luminosity.psd", 0.01),
        pytest.param("blend-modes/effect-multiply.psd", 0.01),
        pytest.param("blend-modes/effect-normal.psd", 0.01),
        pytest.param("blend-modes/effect-overlay.psd", 0.01),
        pytest.param(
            "blend-modes/effect-pin-light.psd",
            0.01,
            marks=pytest.mark.xfail(reason="Pin light is not accurately supported."),
        ),
        pytest.param("blend-modes/effect-saturation.psd", 0.01),
        pytest.param("blend-modes/effect-screen.psd", 0.01),
        pytest.param("blend-modes/effect-soft-light.psd", 0.01),
        pytest.param(
            "blend-modes/effect-subtract.psd",
            0.01,
            marks=pytest.mark.xfail(reason="Subtract is not accurately supported."),
        ),
        pytest.param(
            "blend-modes/effect-vivid-light.psd",
            0.01,
            marks=pytest.mark.xfail(reason="Vivid light is not accurately supported."),
        ),
    ],
)
def test_blend_mode_quality(psd_file: str, quality: float) -> None:
    """Test conversion quality for various blend modes."""
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
        "shapes/rectangle-6-transform-mask.psd",  # Rectangle with transform and mask
        "shapes/star-1.psd",
        "shapes/star-2.psd",
        "shapes/multi-1.psd",  # Union + Subtract
        "shapes/multi-2.psd",  # Union + Subtract + Intersect
        "shapes/multi-3.psd",  # Union + Subtract + Union
        "shapes/multi-4.psd",  # Union + XOR with composite subpaths, this one requires 0.02 threshold
        "shapes/multi-5-mask.psd",  # Multi-shape with mask
        "shapes/multi-5-mask-disabled.psd",  # Multi-shape with disabled mask
    ],
)
def test_shapes(psd_file: str) -> None:
    """Test conversion quality of shape layers."""
    evaluate_quality(psd_file, 0.02)


def test_enable_live_shapes_flag() -> None:
    """Test that disabling live shapes works."""
    psdimage = PSDImage.open(get_fixture("shapes/rectangle-1.psd"))

    converter = Converter(psdimage, enable_live_shapes=True)
    converter.build()
    assert converter.svg.find(".//rect") is not None, (
        "Expected <rect> element in SVG with live shapes enabled."
    )
    assert converter.svg.find(".//path") is None, (
        "Did not expect <path> element in SVG with live shapes enabled."
    )

    converter = Converter(psdimage, enable_live_shapes=False)
    converter.build()
    assert converter.svg.find(".//rect") is None, (
        "Did not expect <rect> element in SVG with live shapes disabled."
    )
    assert converter.svg.find(".//path") is not None, (
        "Expected <path> element in SVG with live shapes disabled."
    )


@pytest.mark.parametrize(
    "psd_file",
    [
        "paint/transparent-1.psd",
        "paint/color-1.psd",
        "paint/color-2.psd",  # Fill opacity test for shape layer
        "paint/color-3.psd",  # Fill opacity test for raster layer
    ],
)
def test_paint_color(psd_file: str) -> None:
    """Test conversion quality for painting."""
    evaluate_quality(psd_file, 0.005)


@pytest.mark.parametrize(
    "psd_file",
    [
        "paint/linear-gradient-1.psd",
        "paint/linear-gradient-2.psd",  # Fill opacity test
        # Gradient interpolation methods: quality may vary.
        "paint/linear-gradient-3-interp-classic.psd",  # Classic interpolation
        "paint/linear-gradient-3-interp-linear.psd",  # Linear interpolation
        "paint/linear-gradient-3-interp-perceptual.psd",  # Perceptual interpolation
        "paint/linear-gradient-3-interp-smooth.psd",  # Smooth interpolation
        pytest.param(
            "paint/linear-gradient-3-interp-stripes.psd",
            marks=pytest.mark.xfail(reason="Stripes interpolation is not supported."),
        ),
        # Gradient alignment tests.
        "paint/linear-gradient-3-align.psd",
        "paint/linear-gradient-3-no-align.psd",
        # Gradient transformation tests.
        "paint/linear-gradient-4-00deg.psd",
        "paint/linear-gradient-4-45deg.psd",
        "paint/linear-gradient-4-90deg.psd",
        "paint/linear-gradient-5-00deg.psd",
        "paint/linear-gradient-5-45deg.psd",
        "paint/linear-gradient-5-90deg.psd",
        "paint/linear-gradient-6-00deg.psd",
        "paint/linear-gradient-6-45deg.psd",
        "paint/linear-gradient-6-90deg.psd",
        # Offset test.
        "paint/linear-gradient-7-offset.psd",
        # Interpolation test.
        "paint/linear-gradient-8-stops.psd",
        # Radial gradients.
        "paint/radial-gradient-1.psd",
    ],
)
def test_paint_gradient(psd_file: str) -> None:
    """Test conversion quality for gradient painting."""
    evaluate_quality(psd_file, 0.005)


@pytest.mark.parametrize(
    "psd_file",
    [
        "paint/pattern-1.psd",
        "paint/pattern-2.psd",  # Transformed pattern
    ],
)
def test_paint_pattern(psd_file: str) -> None:
    """Test conversion quality for pattern painting."""
    evaluate_quality(psd_file, 0.005)


@pytest.mark.parametrize(
    "psd_file",
    [
        "paint/stroke-1-color.psd",
        "paint/stroke-1-gradient.psd",
        "paint/stroke-1-pattern.psd",
    ],
)
def test_paint_stroke(psd_file: str) -> None:
    """Test conversion quality for stroke painting."""
    evaluate_quality(psd_file, 0.005)


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
        "effects/gradient-overlay-7.psd",  # fill layer with overlay effect and offset
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
        # Multiple overlay effects. Priority is color > gradient > pattern.
        "effects/multiple-overlays-1-all.psd",  # All overlay effects together
        "effects/multiple-overlays-1-no-color.psd",  # Without color overlay
        "effects/multiple-overlays-1-duplicate-colors.psd",  # Duplicate color overlays
    ],
)
def test_effects(psd_file: str) -> None:
    """Test effects quality in the raster format."""
    evaluate_quality(psd_file, 0.01)


@pytest.mark.parametrize(
    "psd_file",
    [
        "effects/stroke-1-raster-color.psd",
        "effects/stroke-1-raster-gradient.psd",
        "effects/stroke-1-raster-pattern.psd",
        "effects/stroke-1-vector-color.psd",
        "effects/stroke-1-vector-gradient.psd",
        "effects/stroke-1-vector-pattern.psd",
        "effects/stroke-2-vector-color.psd",  # Stroke around stroke case.
    ],
)
def test_stroke_effects(psd_file: str) -> None:
    """Test stroke effect quality in the raster format."""
    evaluate_quality(psd_file, 0.01)


@pytest.mark.parametrize(
    "psd_file, quality",
    [
        pytest.param(
            "effects/color-overlay-8-text.psd",
            0.05,
            marks=pytest.mark.requires_arial,
        ),
        pytest.param(
            "effects/drop-shadow-7-text.psd",
            0.05,
            marks=pytest.mark.requires_arial,
        ),
        pytest.param(
            "effects/stroke-3-text.psd",
            0.05,
            marks=pytest.mark.requires_arial,
        ),
    ],
)
def test_text_effects_quality(psd_file: str, quality: float) -> None:
    """Test conversion quality for text layers with effects."""
    evaluate_quality(psd_file, quality)


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


@pytest.mark.parametrize(
    "psd_file",
    [
        "adjustments/invert-mask.psd",
        "adjustments/invert-clipping-mask.psd",
        pytest.param(
            "adjustments/invert-clippingbase.psd",
            marks=pytest.mark.xfail(
                reason="Adjustment layer for clipping base is not supported."
            ),
        ),
        pytest.param(
            "adjustments/invert-mask-transparent.psd",
            marks=pytest.mark.xfail(
                reason="Transparency is not supported for adjustment layers."
            ),
        ),
    ],
)
def test_adjustment_invert(psd_file: str) -> None:
    """Test conversion quality of invert adjustment layer."""
    evaluate_quality(psd_file, 0.01)


@pytest.mark.parametrize(
    "psd_file",
    [
        "texts/paragraph-shapetype0-justification0.psd",
        "texts/paragraph-shapetype0-justification1.psd",
        "texts/paragraph-shapetype0-justification2.psd",
    ],
)
def test_text_paragraph_justification(psd_file: str) -> None:
    """Test text paragraph justification handling."""
    # We need a higher threshold depending on the available fonts.
    evaluate_quality(psd_file, 0.02)
