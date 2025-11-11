import logging
import re
import xml.etree.ElementTree as ET
from re import Pattern
from typing import Any, Optional, Sequence


logger = logging.getLogger(__name__)

NAMESPACE = "http://www.w3.org/2000/svg"

ILLEGAL_XML_RE: Pattern[str] = re.compile(
    "[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf\ufffe-\uffff]"
)

DEFAULT_NUMBER_DIGITS = 2


def safe_utf8(text: str) -> str:
    """Remove illegal XML characters from text."""
    return ILLEGAL_XML_RE.sub(" ", text)


def num2str(num: int | float | bool, digit: int = DEFAULT_NUMBER_DIGITS) -> str:
    """Convert a number to a string, using the specified format for floats."""
    if isinstance(num, bool):
        return "true" if num else "false"
    if isinstance(num, int):
        return str(num)
    if isinstance(num, float):
        if num.is_integer():
            return str(int(num))
        # Format float with specified number of digits, and trim trailing zeros
        number = f"{num:.{digit}f}"
        return f"{number[0]}{number[1:].rstrip('0').rstrip('.')}"
    raise ValueError(f"Unsupported type: {type(num)}")


def seq2str(
    seq: Sequence[int | float | bool], sep=",", digit: int = DEFAULT_NUMBER_DIGITS
) -> str:
    """Convert a sequence of numbers to a string, using the specified format for floats."""
    return sep.join(num2str(n, digit) for n in seq)


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
    node = ET.Element(tag)
    if class_:
        node.set("class", class_)
    for key, value in kwargs.items():
        if value is None:
            continue
        key = key.rstrip("_")  # allow trailing underscore for keywords
        key = key.replace("_", "-")  # convert underscores to hyphens
        set_attribute(node, key, value)
    if text:
        node.text = safe_utf8(text)
    if title:
        create_node("title", parent=node, text=safe_utf8(title))
    if desc:
        create_node("desc", parent=node, text=safe_utf8(desc))
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


def add_style(node: ET.Element, key: str, value: Any) -> None:
    """Add a CSS property to an XML node."""
    if "style" in node.attrib:
        node.set("style", f"{node.get('style')}; {key}: {value}")
    else:
        node.set("style", f"{key}: {value}")


def add_class(node: ET.Element, class_name: str) -> None:
    """Add a class to an XML node."""
    if "class" in node.attrib:
        classes = node.get("class", "").split()
        if class_name not in classes:
            classes.append(class_name)
            node.set("class", " ".join(classes))
    else:
        node.set("class", class_name)


def set_attribute(node: ET.Element, key: str, value: Any) -> None:
    """Add an attribute to an XML node."""
    if isinstance(value, (int, float, bool)):
        node.set(key, num2str(value))
    elif isinstance(value, list) and all(
        isinstance(v, (int, float, bool)) for v in value
    ):
        node.set(key, seq2str(value))
    else:
        node.set(key, str(value))


def append_attribute(
    node: ET.Element, key: str, value: Any, separator: str = " "
) -> None:
    """Append a value to an existing attribute of an XML node."""
    if key in node.attrib:
        existing_value = node.get(key, "")
        new_value = f"{existing_value}{separator}{value}"
        node.set(key, new_value)
    else:
        set_attribute(node, key, value)


def get_uri(node: ET.Element) -> str:
    """Get an uri string for the given node."""
    id_ = node.get("id")
    if not id_:
        raise ValueError(f"Node must have an 'id' attribute to get uri: {node}")
    return f"#{id_}"


def get_funciri(node: ET.Element) -> str:
    """Get a funciri string for the given node."""
    return f"url({get_uri(node)})"


def wrap_element(
    node: ET.Element, parent: ET.Element, wrapper: ET.Element
) -> ET.Element:
    """Wrap the given existing node in the wrapper element.
    
    Usage:
        wrapper = svg_utils.create_node("g")
        wrapped_node = svg_utils.wrap_element(node, parent, wrapper)

    Args:
        node: The XML node to be wrapped.
        parent: The parent XML node containing the node to be wrapped.
        wrapper: The wrapper XML node.
    """
    # NOTE: There is no direct way to find a parent from the node.
    if node not in parent:
        raise ValueError("Node is not a child of the given parent.")
    parent.remove(node)
    wrapper.append(node)
    return wrapper
