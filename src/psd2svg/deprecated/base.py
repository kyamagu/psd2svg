import xml.etree.ElementTree as ET
from typing import Protocol

from PIL import Image
from psd_tools import PSDImage


class ConverterProtocol(Protocol):
    """Converter state protocol."""
    psd: PSDImage
    svg: ET.Element
    images: list[Image.Image]