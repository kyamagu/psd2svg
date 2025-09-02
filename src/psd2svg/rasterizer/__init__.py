from importlib import import_module
from typing import Any

from .base_rasterizer import BaseRasterizer


def create_rasterizer(
    name: str = "chromium", *args: Any, **kwargs: Any
) -> BaseRasterizer:
    module_name = f"psd2svg.rasterizer.{name.lower()}_rasterizer"
    class_name = f"{name.capitalize()}Rasterizer"
    cls = getattr(import_module(module_name), class_name)
    assert cls is not None, f"Invalid class name: {class_name}"
    return cls(*args, **kwargs)
