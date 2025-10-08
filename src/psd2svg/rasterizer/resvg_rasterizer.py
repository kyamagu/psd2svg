"""
Resvg-based rasterizer module.

Prerequisite:

    pip install resvg-py

"""

import logging
from io import BytesIO
from typing import Any, Optional, Tuple, Union

import resvg_py
from PIL import Image

from .base_rasterizer import BaseRasterizer

logger = logging.getLogger(__name__)


class ResvgRasterizer(BaseRasterizer):
    """Resvg rasterizer using resvg-py."""

    def __init__(self, dpi: int = 0, **kwargs: Any) -> None:
        """
        Initialize the resvg rasterizer.
        
        Args:
            dpi: Dots per inch for rendering. Default is 96.0.
            **kwargs: Additional arguments (unused but kept for compatibility).
        """
        self.dpi = dpi

    def rasterize(
        self, url: str, size: Optional[Tuple[int, int]] = None, **kwargs: Any
    ) -> Image.Image:
        """
        Rasterize an SVG file to a PIL Image.
        
        Args:
            url: Path to the SVG file.
            size: Optional target size (width, height) in pixels.
            **kwargs: Additional arguments (unused).
            
        Returns:
            PIL Image object containing the rasterized SVG.
        """
        if size:
            # Size parameter is not supported.
            logger.warning("Size parameter is not supported in ResvgRasterizer.")
        png_bytes = resvg_py.svg_to_bytes(svg_path=url, dpi=int(self.dpi))
        image = Image.open(BytesIO(png_bytes))
        return self.composite_background(image)

    def rasterize_from_string(
        self, input: Union[str, bytes], **kwargs: Any
    ) -> Image.Image:
        """
        Rasterize SVG content from a string to a PIL Image.
        
        Args:
            input: SVG content as string or bytes.
            **kwargs: Additional arguments passed to rasterize.
            
        Returns:
            PIL Image object containing the rasterized SVG.
        """
        # Convert bytes to string if necessary
        svg_string = input.decode('utf-8') if isinstance(input, bytes) else input
        png_bytes = resvg_py.svg_to_bytes(svg_string=svg_string, dpi=int(self.dpi))
        image = Image.open(BytesIO(png_bytes))
        return self.composite_background(image)