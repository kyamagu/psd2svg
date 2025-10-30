import numpy as np

from psd2svg.eval import compare_raster_images


def test_compare_raster_images_identical():
    """Test compare_raster_images with identical images."""
    img1 = np.random.rand(100, 100, 4).astype(np.float32)
    img2 = img1.copy()
    assert np.isclose(compare_raster_images(img1, img2, metric="MSE"), 0.0)
    assert np.isclose(compare_raster_images(img1, img2, metric="PSNR"), float("inf"))
    assert np.isclose(compare_raster_images(img1, img2, metric="SSIM"), 1.0)
