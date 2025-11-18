import numpy as np
import pytest

from psd2svg.eval import compare_raster_images

try:
    import skimage  # noqa: F401

    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False


@pytest.mark.parametrize(
    "metric,expected",
    [
        ("MSE", 0.0),
        ("PSNR", float("inf")),
        pytest.param(
            "SSIM",
            1.0,
            marks=pytest.mark.skipif(
                not HAS_SKIMAGE, reason="scikit-image not installed"
            ),
        ),
    ],
)
def test_compare_raster_images_identical(metric, expected):
    """Test compare_raster_images with identical images."""
    img1 = np.random.rand(100, 100, 4).astype(np.float32)
    img2 = img1.copy()
    result = compare_raster_images(img1, img2, metric=metric)
    assert np.isclose(result, expected)
