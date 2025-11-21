import logging

import numpy as np
from psd_tools import PSDImage
from PIL import Image

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


def create_diff_image(psdimage: PSDImage, amplify: float = 1.0) -> Image.Image:
    """Create a diff image between the original and rasterized images for debugging purposes.

    Args:
        psdimage: The PSD image to compare.
        amplify: Multiplier to amplify differences for better visibility. Default is 1.0.

    Returns:
        A PIL Image showing the differences between original and rasterized images.
    """
    rasterized = SVGDocument.from_psd(psdimage).rasterize()
    original = psdimage.composite()
    if original.mode != "RGB":
        original = original.convert("RGB")
    if rasterized.mode != "RGB":
        rasterized = rasterized.convert("RGB")

    diff = np.abs(
        np.array(original, dtype=np.float32) - np.array(rasterized, dtype=np.float32)
    )
    diff = np.clip(diff * amplify, 0, 255).astype(np.uint8)
    return Image.fromarray(diff)


def compare_raster_images(
    input1: np.ndarray | Image.Image,
    input2: np.ndarray | Image.Image,
    metric: str = "MSE",
) -> float:
    """Compare two raster images in numpy array format."""
    input1, input2 = _normalize_images(input1, input2)
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


def _normalize_images(
    input1: np.ndarray | Image.Image, input2: np.ndarray | Image.Image
) -> tuple[np.ndarray, np.ndarray]:
    """Normalize two images to have the same mode and numpy array format."""

    if isinstance(input1, Image.Image) and isinstance(input2, Image.Image):
        if input1.mode != input2.mode:
            logger.debug("Converting image mode: %s -> %s", input2.mode, input1.mode)
            input2 = input2.convert(input1.mode)
    if isinstance(input1, Image.Image):
        input1 = np.array(input1, dtype=np.float32) / 255.0
    if isinstance(input2, Image.Image):
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
    return input1, input2
