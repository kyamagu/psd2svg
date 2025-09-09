import xml.etree.ElementTree as ET
from typing import Protocol

from PIL import Image
from psd_tools import PSDImage
from psd_tools.api import layers


class ConverterProtocol(Protocol):
    """Converter state protocol."""

    psd: PSDImage
    svg: ET.Element
    current: ET.Element
    images: list[Image.Image]

    def add_layer(self, layer: layers.Layer) -> ET.Element | None: ...
    def add_group(self, group: layers.Group) -> ET.Element | None: ...
    def add_pixel(self, layer: layers.Layer) -> ET.Element | None: ...
    def add_shape(self, layer: layers.ShapeLayer) -> ET.Element | None: ...
    def add_adjustment(self, layer: layers.AdjustmentLayer) -> ET.Element | None: ...
    def add_type(self, layer: layers.TypeLayer) -> ET.Element | None: ...

    def auto_id(self, prefix: str = "") -> str: ...