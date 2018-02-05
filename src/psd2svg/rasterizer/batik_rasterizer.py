# -*- coding: utf-8 -*-
"""
Chromium-based rasterizer module.

Prerequisite:

    sudo apt-get install -y chromedriver chromium

"""
from __future__ import absolute_import, unicode_literals

from PIL import Image
import logging
import os
import subprocess
from psd2svg.utils import temporary_directory

logger = logging.getLogger(__name__)


BATIK_PATH = "/usr/share/java/batik-rasterizer.jar"


class BatikRasterizer(object):
    """Batik rasterizer."""

    def __init__(self, jar_path=None, **kwargs):
        self.jar_path = jar_path if jar_path else BATIK_PATH
        assert os.path.exists(self.jar_path)

    def rasterize(self, url, size=None, format="png"):
        with temporary_directory() as d:
            output_file = os.path.join(d, "output.{}".format(format))
            cmd = ["java", "-Djava.awt.headless=true", "-jar", self.jar_path,
                   "{}".format(url), "-d", output_file]
            if size:
                cmd += ["-w", size[0], "-h", size[1]]
            subprocess.check_call(cmd, stdout=subprocess.PIPE)
            assert os.path.exists(output_file)
            return Image.open(output_file)
