from importlib import import_module
from typing import Any

from .base_rasterizer import BaseRasterizer


def create_rasterizer(name: str = "resvg", *args: Any, **kwargs: Any) -> BaseRasterizer:
    module_name = f"psd2svg.rasterizer.{name.lower()}_rasterizer"
    try:
        module = import_module(module_name)
        cls = getattr(module, f"{name.capitalize()}Rasterizer")
    except (ImportError, AttributeError):
        raise RuntimeError(f"Invalid rasterizer name: {name}")
    if cls is None:
        raise RuntimeError(f"Invalid class name: {name}")
    return cls(*args, **kwargs)
