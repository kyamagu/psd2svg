# -*- coding: utf-8 -*-
"""
Inkscape rasterizer module.

Prerequisite:

    sudo apt-get install -y inkscape

"""
from __future__ import absolute_import, unicode_literals

from PIL import Image
import logging
import os
import sys
import subprocess
from psd2svg.utils import temporary_directory
from psd2svg.rasterizer.base_rasterizer import BaseRasterizer

logger = logging.getLogger(__name__)


class InkscapeRasterizer(BaseRasterizer):
    """Inkscape rasterizer."""

    def __init__(self, executable_path="inkscape", **kwargs):
        self.executable_path = executable_path

    def rasterize(self, url, size=None, format="png"):
        with temporary_directory() as tempdir:
            output_file = os.path.join(tempdir, "output.{}".format(format))
            cmd = [os.path.abspath(url), "-e", output_file,
                   "-b" "FFFFFF", "-y", "0"]
            if size:
                cmd += ["-w", size[0], "-h", size[1]]
            proc = subprocess.check_call(
                [self.executable_path, "-z"] + cmd,
                stdout=sys.stdout, stderr=sys.stdout)
            assert os.path.exists(output_file)
            rasterized = Image.open(output_file)
            return self.composite_background(rasterized)
