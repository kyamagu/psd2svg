"""Resvg-based rasterizer module.

This module provides SVG rasterization using the resvg library via resvg-py,
offering fast and accurate rendering with no external dependencies.
"""

import logging
from io import BytesIO
from typing import Union

import resvg_py
from PIL import Image

from .base_rasterizer import BaseRasterizer

logger = logging.getLogger(__name__)


class ResvgRasterizer(BaseRasterizer):
    """High-performance SVG rasterizer using resvg.

    This rasterizer uses the resvg library (via resvg-py) to convert SVG
    documents to raster images. Resvg is a fast, accurate SVG renderer
    written in Rust that provides excellent quality with minimal dependencies.

    Example:
        >>> rasterizer = ResvgRasterizer(dpi=96)
        >>> image = rasterizer.from_file('input.svg')
        >>> image.save('output.png')

        >>> svg_content = '<svg>...</svg>'
        >>> image = rasterizer.from_string(svg_content)
        >>> image.save('output.png')
    """

    def __init__(self, dpi: int = 0) -> None:
        """Initialize the resvg rasterizer.

        Args:
            dpi: Dots per inch for rendering. If 0 (default), uses resvg's
                default of 96 DPI. Higher values produce larger, higher
                resolution images (e.g., 300 DPI for print quality).
        """
        self.dpi = dpi

    def from_file(self, filepath: str) -> Image.Image:
        """Rasterize an SVG file to a PIL Image.

        Args:
            filepath: Path to the SVG file to rasterize.

        Returns:
            PIL Image object in RGBA mode containing the rasterized SVG.

        Raises:
            FileNotFoundError: If the SVG file does not exist.
            ValueError: If the SVG content is invalid.
        """
        png_bytes = resvg_py.svg_to_bytes(svg_path=filepath, dpi=int(self.dpi))
        image = Image.open(BytesIO(png_bytes))
        return self._composite_background(image)

    def from_string(self, svg_content: Union[str, bytes]) -> Image.Image:
        """Rasterize SVG content from a string to a PIL Image.

        This method provides an optimized implementation that directly
        rasterizes the SVG content without creating a temporary file.

        Args:
            svg_content: SVG content as string or bytes.

        Returns:
            PIL Image object in RGBA mode containing the rasterized SVG.

        Raises:
            ValueError: If the SVG content is invalid.
        """
        # Convert bytes to string if necessary
        svg_string = (
            svg_content.decode("utf-8")
            if isinstance(svg_content, bytes)
            else svg_content
        )
        png_bytes = resvg_py.svg_to_bytes(svg_string=svg_string, dpi=int(self.dpi))
        image = Image.open(BytesIO(png_bytes))
        return self._composite_background(image)
