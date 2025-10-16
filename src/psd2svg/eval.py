import logging

import numpy as np
from psd_tools import PSDImage
from PIL.Image import Image

from psd2svg import SVGDocument

logger = logging.getLogger(__name__)


def compute_conversion_quality(psdimage: PSDImage, metric: str) -> float:
    """Test conversion quality in the raster format."""
    rasterized = SVGDocument.from_psd(psdimage).rasterize()
    original = psdimage.composite()
    if original.mode != "RGBA":
        original = original.convert("RGBA")

    # Quality check.
    assert rasterized.width == original.width
    assert rasterized.height == original.height
    assert rasterized.mode == original.mode

    score = compare_raster_images(original, rasterized, metric=metric)
    return score


def compare_raster_images(
    input1: np.ndarray | Image, input2: np.ndarray | Image, metric: str = "MSE"
) -> float:
    """Compare two raster images in numpy array format."""

    if isinstance(input1, Image) and isinstance(input2, Image):
        if input1.mode != input2.mode:
            logger.debug("Converting image mode: %s -> %s", input2.mode, input1.mode)
            input2 = input2.convert(input1.mode)
    if isinstance(input1, Image):
        input1 = np.array(input1, dtype=np.float32) / 255.0
    if isinstance(input2, Image):
        input2 = np.array(input2, dtype=np.float32) / 255.0

    assert input1.shape == input2.shape, (
        "Input images must have the same shape: {} vs {}".format(
            input1.shape,
            input2.shape,
        )
    )
    assert input1.dtype == input2.dtype, (
        "Input images must have the same data type: {} vs {}".format(
            input1.dtype,
            input2.dtype,
        )
    )

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
