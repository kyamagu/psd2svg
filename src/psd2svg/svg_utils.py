import logging
import re
import xml.etree.ElementTree as ET
from re import Pattern
from typing import Any, Optional, Sequence


logger = logging.getLogger(__name__)

NAMESPACE = "http://www.w3.org/2000/svg"
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"

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
    seq: Sequence[int | float | bool],
    sep: str = ",",
    digit: int = DEFAULT_NUMBER_DIGITS,
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


def create_xhtml_node(
    tag: str,
    parent: Optional[ET.Element] = None,
    text: str = "",
    **kwargs: Any,
) -> ET.Element:
    """Create an XHTML node with proper namespace.

    This helper creates elements in the XHTML namespace for use within
    SVG <foreignObject> elements. The namespace is required for proper
    rendering in modern browsers (Chrome, Firefox, Safari, Edge).
    Note: resvg/resvg-py does not support foreignObject rendering.

    Args:
        tag: HTML tag name (e.g., 'div', 'p', 'span').
        parent: Optional parent element to append this node to.
        text: Optional text content.
        **kwargs: Additional attributes. Underscores in keys are converted
                 to hyphens (e.g., 'font_size' becomes 'font-size').

    Returns:
        XHTML element with namespace prefix.

    Example:
        >>> foreign_obj = create_node("foreignObject", x=0, y=0, width=100, height=50)
        >>> div = create_xhtml_node("div", parent=foreign_obj)
        >>> p = create_xhtml_node("p", parent=div, text="Hello")
        >>> span = create_xhtml_node("span", parent=p, text="World", style="color: red")
    """
    # Create element with XHTML namespace
    node = ET.Element(f"{{{XHTML_NAMESPACE}}}{tag}")

    # Set attributes
    for key, value in kwargs.items():
        if value is None:
            continue
        key = key.rstrip("_")  # allow trailing underscore for keywords
        key = key.replace("_", "-")  # convert underscores to hyphens
        set_attribute(node, key, value)

    # Set text content
    if text:
        node.text = safe_utf8(text)

    # Append to parent if provided
    if parent is not None:
        parent.append(node)

    return node


def styles_to_string(styles: dict[str, str]) -> str:
    """Convert a dictionary of CSS styles to a CSS string.

    Args:
        styles: Dictionary of CSS property names to values.

    Returns:
        CSS string suitable for use in a 'style' attribute.

    Example:
        >>> styles = {"color": "red", "font-size": "12px"}
        >>> styles_to_string(styles)
        'color: red; font-size: 12px'
    """
    if not styles:
        return ""
    return "; ".join(f"{key}: {value}" for key, value in styles.items())


def _strip_text_element_whitespace(node: ET.Element) -> None:
    """Strip whitespace-only text and tail from SVG text elements.

    SVG preserves whitespace in text elements by default. When pretty-printing
    adds indentation, this whitespace becomes significant and can cause
    alignment issues (especially with text-anchor="end"). This function ensures
    that any whitespace-only text/tail content is removed from text container
    elements, leaving only the actual text content in tspan children.
    """
    # Check if this is a text or tspan element
    tag = node.tag
    if isinstance(tag, str):
        # Handle namespaced tags
        local_name = tag.split("}")[-1] if "}" in tag else tag
        is_text_element = local_name in ("text", "tspan")
    else:
        is_text_element = False

    if is_text_element:
        # If element has children, clear any whitespace-only text
        if len(node) > 0:
            if node.text and node.text.strip() == "":
                node.text = None

        # Clear whitespace-only tail for all child elements
        for child in node:
            if child.tail and child.tail.strip() == "":
                child.tail = None

    # Recursively clean all child elements
    for child in node:
        _strip_text_element_whitespace(child)


def fromstring(data: str) -> ET.Element:
    """Parse an XML string to an Element."""
    return ET.fromstring(data)


def tostring(node: ET.Element, indent: str = "  ") -> str:
    """Convert an XML node to a string."""
    ET.indent(node, space=indent)
    _strip_text_element_whitespace(node)
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
    _strip_text_element_whitespace(node)
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

    Usage::
        wrapper = svg_utils.create_node("g")
        wrapped_node = svg_utils.wrap_element(node, parent, wrapper)

    Args:
        node: The XML node to be wrapped.
        parent: The parent XML node containing the node to be wrapped.
        wrapper: The wrapper XML node.
    """
    # NOTE: There is no direct way to find a parent from the node.
    if node not in parent:
        raise ValueError(f"Node is not a child of the given parent: {node} in {parent}")
    parent.remove(node)
    wrapper.append(node)
    return wrapper


def merge_attribute_less_children(element: ET.Element) -> None:
    """Recursively merge children without attributes into their parent nodes.

    This utility removes redundant wrapper elements that have no attributes,
    moving their text content directly into the parent element. This helps
    produce cleaner, more compact SVG output.

    The function preserves document order by properly handling both element.text
    and child.tail to ensure text appears in the correct sequence.

    Args:
        element: The XML element to process recursively.

    Example:
        Before: <text><tspan x="10"><tspan>Hello</tspan></tspan></text>
        After:  <text><tspan x="10">Hello</tspan></text>

        Before: <text><tspan font-weight="700">Bold</tspan><tspan> text</tspan></text>
        After:  <text><tspan font-weight="700">Bold</tspan> text</text>
    """
    # First, recursively process all children
    for child in list(element):
        merge_attribute_less_children(child)

    # Then merge attribute-less children into parent
    # We need to find the previous element that still exists (wasn't removed)
    children = list(element)
    for i, child in enumerate(children):
        if not child.attrib:
            # Move child's text content
            if child.text:
                # Find previous sibling that still exists in the tree
                prev_existing = None
                for j in range(i - 1, -1, -1):
                    if children[j] in element:
                        prev_existing = children[j]
                        break

                if prev_existing is not None:
                    # Append to previous existing sibling's tail
                    prev_existing.tail = (prev_existing.tail or "") + child.text
                else:
                    # No previous sibling, append to parent's text
                    element.text = (element.text or "") + child.text

            # Move child's tail
            if child.tail:
                # Find next sibling that still exists in the tree
                next_existing = None
                for j in range(i + 1, len(children)):
                    if children[j] in element:
                        next_existing = children[j]
                        break

                if next_existing is not None:
                    # Prepend to next existing sibling's text
                    next_existing.text = child.tail + (next_existing.text or "")
                else:
                    # No next sibling, find previous sibling or append to parent
                    prev_existing = None
                    for j in range(i - 1, -1, -1):
                        if children[j] in element:
                            prev_existing = children[j]
                            break

                    if prev_existing is not None:
                        prev_existing.tail = (prev_existing.tail or "") + child.tail
                    else:
                        element.text = (element.text or "") + child.tail

            # Remove the now-empty child
            element.remove(child)


def merge_common_child_attributes(
    element: ET.Element, excludes: set[str] | None = None
) -> None:
    """Recursively merge common child attributes to their parent node.

    This utility hoists attributes that are common to ALL children (with the same value)
    to the parent element. This helps produce cleaner, more compact SVG output by
    reducing redundant attribute declarations.

    Args:
        element: The XML element to process recursively.
        excludes: Set of attribute names that should not be hoisted to parent.
                 Common excludes for text elements: {"x", "y", "dx", "dy", "transform"}

    Example:
        Before: <text><tspan fill="red">A</tspan><tspan fill="red">B</tspan></text>

        After:  <text fill="red"><tspan>A</tspan><tspan>B</tspan></text>

        Before (with excludes={"x"}):
                <text><tspan x="10" fill="red">A</tspan><tspan x="20" fill="red">B</tspan></text>

        After:  <text fill="red"><tspan x="10">A</tspan><tspan x="20">B</tspan></text>
    """
    if excludes is None:
        excludes = set()

    # First, recursively process all children
    for child in list(element):
        merge_common_child_attributes(child, excludes)

    # Find attributes that all children have in common with the same value
    children = list(element)
    if not children:
        return

    # Start with the first child's attributes as candidates
    common_attribs: dict[str, str] = {
        key: value for key, value in children[0].attrib.items() if key not in excludes
    }

    # Check if remaining children all have the same values
    for child in children[1:]:
        keys_to_remove = []
        for key in common_attribs:
            if key not in child.attrib or child.attrib[key] != common_attribs[key]:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del common_attribs[key]

    # Migrate the common attributes to the parent element
    for key, value in common_attribs.items():
        element.attrib[key] = value
        for child in element:
            del child.attrib[key]


def merge_singleton_children(element: ET.Element) -> None:
    """Recursively merge singleton child nodes into their parent nodes.

    This utility removes redundant wrapper elements when a parent has exactly one child
    and there are no conflicting attributes. The child's attributes and text content
    are moved to the parent element.

    Args:
        element: The XML element to process recursively.

    Example:
        Before: <text><tspan>Hello</tspan></text>
        After:  <text>Hello</text>

        Before: <text x="10"><tspan font-weight="700">Bold</tspan></text>
        After:  <text x="10" font-weight="700">Bold</text>

        Not merged (conflicting attributes):
        Before: <text x="10"><tspan x="20">Text</tspan></text>
        After:  <text x="10"><tspan x="20">Text</tspan></text>  (unchanged)
    """
    # First, recursively process all children
    for child in list(element):
        merge_singleton_children(child)

    # Merge singleton child if present
    if len(element) == 1:
        child = element[0]

        # Check for attribute conflicts
        if len(set(element.attrib.keys()) & set(child.attrib.keys())) > 0:
            return  # Conflicting attributes, do not merge

        # Move child's text content to parent
        # Note: child.text comes before any children in document order
        if child.text:
            element.text = (element.text or "") + child.text

        # Move child's tail to parent's text
        # Note: When we remove the child, its tail (which comes after </child>)
        # should become part of the parent's text content
        if child.tail:
            element.text = (element.text or "") + child.tail

        # Move all child's attributes to parent
        for key, value in child.attrib.items():
            element.attrib[key] = value

        # Remove the now-merged child
        element.remove(child)


def consolidate_defs(svg: ET.Element) -> None:
    """Consolidate all <defs> and definition elements into a global <defs>.

    This optimization improves SVG structure by:
    1. Creating a single global <defs> element at the beginning of the SVG
    2. Moving all definition elements (filters, gradients, patterns, etc.) into it
    3. Removing now-empty inline <defs> elements

    Definition elements that are moved:
    - <defs> (contents merged into global defs)
    - <filter>
    - <linearGradient>
    - <radialGradient>
    - <pattern>
    - <clipPath>
    - <marker>
    - <symbol>

    Args:
        svg: The root SVG element to optimize (modified in-place).

    Note:
        This function preserves all id references and element ordering within defs.
        It does NOT move <mask> elements as they can contain rendered content.

    Example:
        Before:
            <svg>
                <rect fill="url(#g1)"/>
                <linearGradient id="g1">...</linearGradient>
                <defs><filter id="f1">...</filter></defs>
            </svg>

        After:
            <svg>
                <defs>
                    <linearGradient id="g1">...</linearGradient>
                    <filter id="f1">...</filter>
                </defs>
                <rect fill="url(#g1)"/>
            </svg>
    """
    # Definition element tags to consolidate (without namespace)
    definition_tags = {
        "filter",
        "linearGradient",
        "radialGradient",
        "pattern",
        "clipPath",
        "marker",
        "symbol",
    }

    # Find or create global <defs> element at the beginning
    global_defs = None
    for child in svg:
        tag = child.tag
        local_name = tag.split("}")[-1] if "}" in tag else tag
        if local_name == "defs":
            global_defs = child
            break

    if global_defs is None:
        # Create new global defs as first child
        global_defs = ET.Element("defs")
        svg.insert(0, global_defs)
    else:
        # Ensure global_defs is the first child
        if svg[0] is not global_defs:
            svg.remove(global_defs)
            svg.insert(0, global_defs)

    # Collect all definition elements from the entire SVG tree
    definitions_to_move: list[tuple[ET.Element, ET.Element]] = []  # (element, parent)

    def collect_definitions(element: ET.Element) -> None:
        """Recursively collect definition elements to move."""
        for child in list(element):
            tag = child.tag
            local_name = tag.split("}")[-1] if "}" in tag else tag

            # If it's a <defs> element (not the global one), collect its children
            if local_name == "defs" and child is not global_defs:
                for def_child in list(child):
                    definitions_to_move.append((def_child, child))
                # Continue recursing into defs (in case of nested structures)
                collect_definitions(child)
            # If it's a definition element (not inside global defs), collect it
            elif local_name in definition_tags and element is not global_defs:
                definitions_to_move.append((child, element))
                # Still recurse into the element (e.g., filters can contain other elements)
                collect_definitions(child)
            else:
                # Recurse into other elements
                collect_definitions(child)

    # Collect definitions directly from SVG root level
    for child in list(svg):
        if child is global_defs:
            continue

        tag = child.tag
        local_name = tag.split("}")[-1] if "}" in tag else tag

        # If it's a <defs> element, collect its children
        if local_name == "defs":
            for def_child in list(child):
                definitions_to_move.append((def_child, child))
            # Also recurse into it
            collect_definitions(child)
        # If it's a definition element, collect it
        elif local_name in definition_tags:
            definitions_to_move.append((child, svg))
            # Also recurse into it
            collect_definitions(child)
        else:
            # For non-definition elements, recurse to find nested definitions
            collect_definitions(child)

    # Move all collected definitions to global defs
    for element, parent in definitions_to_move:
        # Skip if element has already been moved (e.g., parent was removed)
        if element not in parent:
            continue
        parent.remove(element)
        global_defs.append(element)

    # Remove now-empty <defs> elements
    def remove_empty_defs(element: ET.Element) -> None:
        """Recursively remove empty <defs> elements."""
        for child in list(element):
            tag = child.tag
            local_name = tag.split("}")[-1] if "}" in tag else tag
            if local_name == "defs" and child is not global_defs and len(child) == 0:
                element.remove(child)
            else:
                remove_empty_defs(child)

    remove_empty_defs(svg)

    # Remove global defs if it's empty (no definitions were found)
    if len(global_defs) == 0:
        svg.remove(global_defs)
