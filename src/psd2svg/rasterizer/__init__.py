# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from importlib import import_module


def create_rasterizer(name="chromium", *args, **kwargs):
    module_name = "psd2svg.rasterizer.{}_rasterizer".format(name.lower())
    class_name = "{}Rasterizer".format(name.capitalize())
    cls = getattr(import_module(module_name), class_name)
    assert cls is not None, "Invalid class name: {}".format(class_name)
    return cls(*args, **kwargs)
