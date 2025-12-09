"""Resvg-based rasterizer module.

This module provides SVG rasterization using the resvg library via resvg-py,
offering fast and accurate rendering with no external dependencies.
"""

import logging
import re
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

    Note:
        Resvg does not support CSS @font-face rules with embedded fonts (data URIs).
        This implementation automatically extracts font file paths from @font-face
        src: url("file://...") declarations and passes them to resvg's native font
        loading API. The @font-face CSS rules themselves are ignored by resvg.
        Data URIs (data:font/...) are not supported and will be silently ignored.

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

    @staticmethod
    def _extract_font_file_paths(svg_content: str) -> list[str]:
        """Extract font file paths from @font-face CSS rules in SVG.

        Args:
            svg_content: SVG content as string.

        Returns:
            List of font file paths found in src: url("file://...") declarations.
        """
        font_files = []
        # Pattern to match: src: url("file:///path/to/font.ttf")
        pattern = re.compile(r'src:\s*url\(["\']?(file://[^"\')]+)["\']?\)')

        matches = pattern.findall(svg_content)
        for match in matches:
            # Remove file:// prefix to get the actual path
            font_path = match.replace("file://", "")
            font_files.append(font_path)

        return font_files

    def from_file(
        self, filepath: str, font_files: list[str] | None = None
    ) -> Image.Image:
        """Rasterize an SVG file to a PIL Image.

        Args:
            filepath: Path to the SVG file to rasterize.
            font_files: Optional list of font file paths to use for rendering.

        Returns:
            PIL Image object in RGBA mode containing the rasterized SVG.

        Raises:
            FileNotFoundError: If the SVG file does not exist.
            ValueError: If the SVG content is invalid.
        """
        png_bytes = resvg_py.svg_to_bytes(
            svg_path=filepath, dpi=int(self.dpi), font_files=font_files
        )
        image = Image.open(BytesIO(png_bytes))
        return self._composite_background(image)

    def from_string(
        self, svg_content: Union[str, bytes], font_files: list[str] | None = None
    ) -> Image.Image:
        """Rasterize SVG content from a string to a PIL Image.

        This method provides an optimized implementation that directly
        rasterizes the SVG content without creating a temporary file.

        If font_files is not provided, this method automatically extracts
        font file paths from @font-face CSS rules in the SVG content
        (file:// URLs).

        Args:
            svg_content: SVG content as string or bytes.
            font_files: Optional list of font file paths to use for rendering.
                If None, font paths are extracted from the SVG content.

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

        # Auto-extract font files from @font-face CSS if not provided
        if font_files is None:
            font_files = self._extract_font_file_paths(svg_string)
            if font_files:
                logger.debug(f"Extracted {len(font_files)} font file(s) from SVG")

        png_bytes = resvg_py.svg_to_bytes(
            svg_string=svg_string, dpi=int(self.dpi), font_files=font_files
        )
        image = Image.open(BytesIO(png_bytes))
        return self._composite_background(image)
