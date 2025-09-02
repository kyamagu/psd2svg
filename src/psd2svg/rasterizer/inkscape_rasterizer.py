"""
Inkscape rasterizer module.

Prerequisite:

    sudo apt-get install -y inkscape

"""

import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Optional, Tuple

from PIL import Image

from psd2svg.rasterizer.base_rasterizer import BaseRasterizer

logger = logging.getLogger(__name__)


class InkscapeRasterizer(BaseRasterizer):
    """Inkscape rasterizer."""

    def __init__(self, executable_path: str = "inkscape", **kwargs: Any) -> None:
        self.executable_path = executable_path

    def rasterize(
        self, url: str, size: Optional[Tuple[int, int]] = None, format: str = "png"
    ) -> Image.Image:
        with tempfile.TemporaryDirectory() as tempdir:
            output_file = os.path.join(tempdir, f"output.{format}")
            cmd = [os.path.abspath(url), "-e", output_file, "-bFFFFFF", "-y", "0"]
            if size:
                cmd += ["-w", size[0], "-h", size[1]]
            proc = subprocess.check_call(
                [self.executable_path, "-z"] + cmd, stdout=sys.stdout, stderr=sys.stdout
            )
            assert os.path.exists(output_file)
            rasterized = Image.open(output_file)
            return self.composite_background(rasterized)
