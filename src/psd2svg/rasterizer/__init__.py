"""Rasterizer module for converting SVG to raster images.

This module provides the ResvgRasterizer for converting SVG documents
to PIL Images using the resvg rendering engine, and optionally the
PlaywrightRasterizer for browser-based rendering with full SVG 2.0 support.
"""

from .base_rasterizer import BaseRasterizer
from .playwright_rasterizer import PlaywrightRasterizer
from .resvg_rasterizer import ResvgRasterizer

__all__ = ["BaseRasterizer", "PlaywrightRasterizer", "ResvgRasterizer"]
