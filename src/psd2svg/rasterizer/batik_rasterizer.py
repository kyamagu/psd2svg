# -*- coding: utf-8 -*-
"""
Batik-based rasterizer module.

Download the latest batik rasterizer to use the module. Note Ubuntu 16.04LTS
package is broken and does not work.

Prerequisite:

    wget http://www.apache.org/dyn/mirrors/mirrors.cgi?action=download&\
    filename=xmlgraphics/batik/binaries/batik-bin-1.9.tar.gz
    export BATIK_PATH=./batik-bin-1.9.tar.gz

Deb package:

    sudo apt-get install -y libbatik-java


"""
from __future__ import absolute_import, unicode_literals

from PIL import Image
import logging
import os
import subprocess
from psd2svg.utils import temporary_directory
from psd2svg.rasterizer.base_rasterizer import BaseRasterizer

logger = logging.getLogger(__name__)


BATIK_PATH = os.environ.get(
    'BATIK_PATH', "/usr/share/java/batik-rasterizer.jar")


class BatikRasterizer(BaseRasterizer):
    """Batik rasterizer."""

    def __init__(self, jar_path=None, **kwargs):
        self.jar_path = jar_path if jar_path else BATIK_PATH
        assert os.path.exists(self.jar_path)

    def rasterize(self, url, size=None, format="png"):
        with temporary_directory() as d:
            output_file = os.path.join(d, "output.{}".format(format))
            cmd = ["java", "-Djava.awt.headless=true",
                   "-jar", self.jar_path,
                   "-bg", "0.255.255.255",
                   "-d", output_file,
                   "{}".format(url),
                   ]
            if size:
                cmd += ["-w", size[0], "-h", size[1]]
            subprocess.check_call(cmd, stdout=subprocess.PIPE)
            assert os.path.exists(output_file)
            rasterized = Image.open(output_file)
            return self.composite_background(rasterized)
