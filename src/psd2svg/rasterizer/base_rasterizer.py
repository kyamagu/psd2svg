# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import tempfile
from PIL import Image

logger = logging.getLogger(__name__)


class BaseRasterizer(object):
    """Base class for rasterizer implementation."""

    def rasterize_from_string(self, input, **kwargs):
        with tempfile.NamedTemporaryFile(suffix='.svg') as f:
            f.write(input if isinstance(input, bytes)
                    else input.encode('utf-8'))
            f.flush()
            return self.rasterize(f.name, **kwargs)

    def rasterize(self, url, size=None, **kwargs):
        raise NotImplementedError

    def composite_background(self, image):
        background = Image.new(
            "RGBA", size=image.size, color=(255, 255, 255, 0))
        background.alpha_composite(image)
        return background
