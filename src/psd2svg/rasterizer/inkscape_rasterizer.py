# -*- coding: utf-8 -*-
"""
Inkscape rasterizer module.

Prerequisite:

    sudo apt-get install -y inkscape

"""
from __future__ import absolute_import, unicode_literals

from PIL import Image
import contextlib
import tempfile
import logging
import os
import shutil
import sys
import subprocess

logger = logging.getLogger(__file__)


@contextlib.contextmanager
def temporary_directory(*args, **kwargs):
    d = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        shutil.rmtree(d)


class InkscapeRasterizer(object):
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
            canvas = Image.new("RGBA", size=rasterized.size,
                               color=(255, 255, 255, 0))
            canvas.alpha_composite(rasterized)
            return canvas
