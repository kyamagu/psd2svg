"""Rasterizer module for converting SVG to raster images.

This module provides the ResvgRasterizer for converting SVG documents
to PIL Images using the resvg rendering engine.
"""

from .base_rasterizer import BaseRasterizer
from .resvg_rasterizer import ResvgRasterizer

__all__ = ["BaseRasterizer", "ResvgRasterizer"]
