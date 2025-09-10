"""
Chromium-based rasterizer module.

Prerequisite:

    sudo apt-get install -y chromedriver chromium

"""

import json
import logging
import math
import os
import re
from io import BytesIO
from typing import Any, Optional, Tuple

from PIL import Image
from selenium import webdriver

from psd2svg.rasterizer.base_rasterizer import BaseRasterizer

logger = logging.getLogger(__name__)


# CHROMEDRIVER_PATH = "/usr/lib/chromium-browser/chromedriver"
VIEWPORT_SIZE: tuple[int, int] = (16, 16)  # Default size when nothing is specified.


# https://stackoverflow.com/questions/46656622/
def send(
    driver: webdriver.Chrome, cmd: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    resource = f"/session/{driver.session_id}/chromium/send_command_and_get_result"
    url = driver.command_executor._url + resource
    body = json.dumps({"cmd": cmd, "params": params or {}})
    response = driver.command_executor._request("POST", url, body)
    if response["status"]:
        raise Exception(response.get("value"))
    return response.get("value")


class ChromiumRasterizer(BaseRasterizer):
    """Chromium rasterizer."""

    def __init__(
        self, executable_path: str = "chromedriver", dpi: float = 96.0, **kwargs: Any
    ) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        options.add_argument("disable-gpu")
        options.add_argument("disable-infobars")
        options.add_argument("no-sandbox")
        options.add_argument("disable-dev-shm-usage")
        options.add_argument("enable-experimental-web-platform-features")
        options.add_argument("default-background-color FFFFFF00")
        self.driver = webdriver.Chrome(executable_path=executable_path, options=options)
        self.dpi = dpi
        self.driver.execute_cdp_cmd(
            "Emulation.setDefaultBackgroundColorOverride",
            {"color": {"r": 255, "g": 255, "b": 255, "a": 0}},
        )

    def __del__(self) -> None:
        self.driver.quit()

    def rasterize(
        self, url: str, size: Optional[Tuple[int, int]] = None, **kwargs: Any
    ) -> Image.Image:
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
            logger.info(
                f"Resizing captured screenshot from {rasterized.size} to {size}"
            )
            rasterized = rasterized.resize(size, Image.NEAREST)
        return self.composite_background(rasterized)

    def _set_windowsize(self) -> Optional[Tuple[int, int]]:
        svg = self.driver.find_element_by_tag_name("svg")
        if not svg:
            raise RuntimeError("No <svg> element found.")
        width = svg.get_attribute("width")
        height = svg.get_attribute("height")
        if not width or not height:
            raise RuntimeError("No width or height attribute found.")
        logger.debug(f"Resizing to {width}x{height}")
        width = self._get_pixels(width)
        height = self._get_pixels(height)
        if width == 0 or height == 0:
            width, height = VIEWPORT_SIZE
        self.driver.set_window_size(int(width), int(height))
        return width, height

    def _get_pixels(self, value: str) -> int:
        match = re.match(r"(?P<value>\d+)(?P<unit>\D+)?", value)
        value = int(match.group("value"))
        unit = match.group("unit")
        if unit == "pt":
            value = math.ceil(value * self.dpi / 72.0)
        return value
