# -*- coding: utf-8 -*-
"""
Chromium-based rasterizer module.

Prerequisite:

    sudo apt-get install -y chromedriver chromium

"""
from __future__ import absolute_import, unicode_literals

from selenium import webdriver
from PIL import Image
from io import BytesIO
import logging
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


# CHROMEDRIVER_PATH = "/usr/lib/chromium-browser/chromedriver"
VIEWPORT_SIZE = (16, 16)  # Default size when nothing is specified.


class ChromiumRasterizer(object):
    """Chromium rasterizer."""

    def __init__(self, executable_path="chromedriver", dpi=96.0, **kwargs):
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        options.add_argument("disable-gpu")
        options.add_argument("disable-infobars")
        options.add_argument("enable-experimental-web-platform-features")
        options.add_argument("default-background-color FFFFFF00")
        self.driver = webdriver.Chrome(
            executable_path=executable_path,
            chrome_options=options)
        self.dpi = dpi

    def __del__(self):
        self.driver.quit()

    def rasterize(self, url, size=None):
        if not re.match(r"^(\S+)://.*$", url):
            url = "file://" + os.path.abspath(url)
        if size:
            self.driver.set_window_size(*size)
            self.driver.get(url)
        else:
            self.driver.get(url)
            size = self._set_windowsize()
        rasterized = Image.open(BytesIO(self.driver.get_screenshot_as_png()))
        if rasterized.width != size[0] or rasterized.height != size[1]:
            logger.info("Resizing captured screenshot from {} to {}".format(
                rasterized.size, size))
            rasterized = rasterized.resize(size, Image.NEAREST)
        canvas = Image.new("RGBA", size=rasterized.size,
                           color=(255, 255, 255, 0))
        canvas.alpha_composite(rasterized)
        return canvas

    def _set_windowsize(self):
        svg = self.driver.find_element_by_tag_name("svg")
        if not svg:
            return
        width = svg.get_attribute("width")
        height = svg.get_attribute("height")
        if not width or not height:
            return
        logger.debug("Resizing to {}x{}".format(width, height))
        width = self._get_pixels(width)
        height = self._get_pixels(height)
        if width == 0 or height == 0:
            width, height = VIEWPORT_SIZE
        self.driver.set_window_size(int(width), int(height))
        return width, height

    def _get_pixels(self, value):
        match = re.match(r"(?P<value>\d+)(?P<unit>\D+)?", value)
        value = int(match.group("value"))
        unit = match.group("unit")
        if unit == "pt":
            value = math.ceil(value * self.dpi / 72.0)
        return value
