# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
from PIL import Image

logger = logging.getLogger(__name__)


class BaseRasterizer(object):
    """Base class for rasterizer implementation."""

    def rasterize(self, url, size=None, **kwargs):
        raise NotImplementedError

    def composite_background(self, image):
        background = Image.new(
            "RGBA", size=image.size, color=(255, 255, 255, 0))
        background.alpha_composite(image)
        return background
