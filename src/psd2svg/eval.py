import logging

import numpy as np
import psd_tools

from psd2svg.rasterizer import create_rasterizer

logger = logging.getLogger(__name__)


def check_quality(psdimage: psd_tools.PSDImage, svg: str, metric: str) -> float:
    """Test conversion quality in the raster format."""

    # Rasterize SVG and compare with original PSD.
    rasterizer = create_rasterizer()
    rasterized = rasterizer.rasterize_from_string(svg)
    original = psdimage.composite()
    if original.mode != "RGBA":
        original = original.convert("RGBA")

    # Quality check.
    assert rasterized.width == original.width
    assert rasterized.height == original.height
    assert rasterized.mode == original.mode

    rasterized_array = np.array(rasterized, dtype=np.float32) / 255.0
    original_array = np.array(original, dtype=np.float32) / 255.0
    score = compare_raster_images(original_array, rasterized_array, metric=metric)
    return score


def compare_raster_images(
    input1: np.ndarray, input2: np.ndarray, metric: str = "MSE"
) -> float:
    """Compare two raster images in numpy array format."""

    assert input1.shape == input2.shape, "Input images must have the same shape."
    assert input1.dtype == input2.dtype, "Input images must have the same data type."

    if input1.dtype == np.uint8:
        input1 = input1.astype(np.float32) / 255.0
    if input2.dtype == np.uint8:
        input2 = input2.astype(np.float32) / 255.0

    metric = metric.upper()
    if metric == "MSE":
        mse = np.nanmean((input1 - input2) ** 2)
        return mse
    elif metric == "PSNR":
        mse = np.nanmean((input1 - input2) ** 2)
        if mse == 0:
            return float("inf")
        psnr = 20 * np.log10(1.0 / np.sqrt(mse))
        return psnr
    elif metric == "SSIM":
        try:
            from skimage.metrics import structural_similarity
        except ImportError:
            raise ImportError("SSIM metric requires scikit-image package")

        ssim, _ = structural_similarity(
            input1,
            input2,
            channel_axis=-1,
            full=True,
            data_range=1.0,
        )
        return ssim
    else:
        raise ValueError(f"Unknown metric: {metric}")
