import base64
import logging
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Any, Optional

from PIL import Image

logger = logging.getLogger(__name__)

NAMESPACE = "http://www.w3.org/2000/svg"


def create_node(
    tag: str,
    parent: Optional[ET.Element] = None,
    class_: str = "",
    title: str = "",
    text: str = "",
    desc: str = "",
    **kwargs: Any,
) -> ET.Element:
    """Create an XML node with attributes."""
    node = ET.Element(tag, attrib={k: str(v) for k, v in kwargs.items() if v})
    if class_:
        node.set("class", class_)
    if text:
        node.text = text
    if title:
        create_node("title", parent=node, text=title)
    if desc:
        create_node("desc", parent=node, text=desc)
    if parent is not None:
        parent.append(node)
    return node


def fromstring(data: str) -> ET.Element:
    """Parse an XML string to an Element."""
    return ET.fromstring(data)


def tostring(node: ET.Element, indent: str = "  ") -> str:
    """Convert an XML node to a string."""
    ET.indent(node, space=indent)
    return ET.tostring(node, encoding="unicode", xml_declaration=False)


def parse(file: Any) -> ET.Element:
    """Parse an XML file to an Element."""
    tree = ET.parse(file)
    if tree is None or tree.getroot() is None:
        raise ValueError("Failed to parse XML file.")
    return tree.getroot()


def write(node: ET.Element, file: Any, indent: str = "  ") -> None:
    """Write an XML node to a file."""
    tree = ET.ElementTree(node)
    ET.indent(tree, space=indent)
    tree.write(file, encoding="unicode", xml_declaration=False)


def encode_data_uri(image: Image.Image, format: str = "PNG") -> str:
    """Encode a PIL image as a base64 data URI."""

    with BytesIO() as buffer:
        image.save(buffer, format=format)
        base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/{format.lower()};base64,{base64_data}"


def add_style(node: ET.Element, key: str, value: Any) -> None:
    """Add a CSS property to an XML node."""
    if "style" in node.attrib:
        node.set("style", f"{node.get('style')}; {key}: {value}")
    else:
        node.set("style", f"{key}: {value}")
