"""
Batik-based rasterizer module.

Download the latest batik rasterizer to use the module. Note Ubuntu 16.04LTS
package is broken and does not work.

Prerequisite:

    wget http://www.apache.org/dyn/mirrors/mirrors.cgi?action=download&\
    filename=xmlgraphics/batik/binaries/batik-bin-1.9.tar.gz
    tar xzf batik-bin-1.9.tar.gz
    export BATIK_PATH=./batik-bin-1.9

Deb package:

    sudo apt-get install -y libbatik-java


"""

import logging
import os
import subprocess
import tempfile
from typing import Any, Optional

from PIL import Image

from psd2svg.rasterizer.base_rasterizer import BaseRasterizer

logger = logging.getLogger(__name__)

BATIK_PATH: str = os.environ.get("BATIK_PATH", "/usr/share/java/batik-rasterizer.jar")


class BatikRasterizer(BaseRasterizer):
    """Batik rasterizer."""

    def __init__(self, jar_path: Optional[str] = None, **kwargs: Any) -> None:
        self.jar_path = jar_path if jar_path else BATIK_PATH
        assert os.path.exists(self.jar_path)

    def rasterize(
        self,
        url: str,
        size: Optional[tuple[int, int]] = None,
        format: str = "png",
        **kwargs: Any,
    ) -> Image.Image:
        with tempfile.TemporaryDirectory() as d:
            basename, ext = os.path.splitext(os.path.basename(url))
            output_file = os.path.join(d, f"{basename}.{format}")
            cmd = [
                "java",
                "-Djava.awt.headless=true",
                "-jar",
                self.jar_path,
                "-bg",
                "0.255.255.255",
                "-m",
                f"image/{format}",
                "-d",
                d,
                f"{url}",
            ]
            if size is not None:
                cmd += ["-w", f"{size[0]}", "-h", f"{size[1]}"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            try:
                assert os.path.exists(output_file)
                rasterized = Image.open(output_file)
            except:
                logger.error(
                    "{}\n{}{}".format(" ".join(cmd), stdout.decode(), stderr.decode())
                )
                raise
            return self.composite_background(rasterized)
