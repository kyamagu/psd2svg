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


def set_transform_with_origin(
    element: ET.Element,
    transform_attr: str,
    transforms: list[str],
    origin: tuple[float, float] | None = None,
) -> None:
    """Set transform attribute with optional transform-origin.

    This function sets transform operations on gradient, pattern, or other SVG elements
    using the modern SVG 2.0 transform-origin attribute instead of translate wrappers.

    Args:
        element: SVG element to modify (e.g., linearGradient, pattern)
        transform_attr: Name of the transform attribute (e.g., "gradientTransform", "patternTransform")
        transforms: List of transform functions (e.g., ['rotate(45)', 'scale(2)'])
        origin: Transform origin point (x, y). If provided, sets transform-origin attribute.
                Default SVG transform-origin is (0, 0).

    Example:
        Instead of: gradientTransform="translate(50,50) rotate(45) translate(-50,-50)"
        Produces:   gradientTransform="rotate(45)" transform-origin="50 50"

    Note:
        SVG 2.0 feature. Supported by modern browsers and resvg-py.
        When origin is provided but no transforms, uses translate() instead.
        When the attribute already exists (from append_attribute), appends to it instead.
    """
    if transforms:
        # Check if there's already a transform attribute (e.g., from offset)
        has_existing = transform_attr in element.attrib

        if has_existing and origin is not None and origin != (0.0, 0.0):
            # If there's an existing transform (e.g., offset), we can't use transform-origin
            # because it would apply to all transforms. Use the old translate pattern instead.
            append_attribute(
                element,
                transform_attr,
                f"translate({seq2str(origin, sep=',', digit=4)})",
            )
            append_attribute(element, transform_attr, " ".join(transforms))
            append_attribute(
                element,
                transform_attr,
                f"translate({seq2str((-origin[0], -origin[1]), sep=',', digit=4)})",
            )
        elif origin is not None and origin != (0.0, 0.0):
            # No existing transform, use transform-origin
            set_attribute(element, transform_attr, " ".join(transforms))
            set_attribute(element, "transform-origin", seq2str(origin, sep=" "))
        else:
            # No origin or origin is (0, 0)
            if has_existing:
                append_attribute(element, transform_attr, " ".join(transforms))
            else:
                set_attribute(element, transform_attr, " ".join(transforms))
    elif origin is not None and origin != (0.0, 0.0):
        # If we have origin but no transforms, use translate instead
        set_attribute(element, transform_attr, f"translate({seq2str(origin)})")


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


def _unwrap_wrapper_element(
    parent: ET.Element,
    wrapper: ET.Element,
    insert_position: int | None = None,
) -> None:
    """Unwrap a wrapper element by moving its children to parent level.

    This helper function is shared by merge_singleton_children and
    merge_attribute_less_children to eliminate code duplication.

    Args:
        parent: Parent element containing the wrapper.
        wrapper: Wrapper element to unwrap (will be removed from parent).
        insert_position: If None, append grandchildren to end of parent;
                        else insert at this position.

    The function:
    - Removes the wrapper from parent
    - Moves wrapper's children (grandchildren) to parent level
    - Transfers wrapper's tail to the last grandchild (or parent's text)
    - Preserves document order
    """
    grandchildren = list(wrapper)

    # Remove wrapper from parent
    parent.remove(wrapper)

    # Insert grandchildren at appropriate position
    if insert_position is None:
        # Append to end (used by merge_singleton_children)
        for grandchild in grandchildren:
            parent.append(grandchild)
    else:
        # Insert at specific position (used by merge_attribute_less_children)
        for j, grandchild in enumerate(grandchildren):
            parent.insert(insert_position + j, grandchild)

    # Transfer wrapper's tail to last grandchild
    if wrapper.tail:
        if len(grandchildren) > 0:
            # Add to last grandchild's tail
            if insert_position is None:
                last_grandchild = parent[-1]
            else:
                last_grandchild = parent[insert_position + len(grandchildren) - 1]
            last_grandchild.tail = (last_grandchild.tail or "") + wrapper.tail
        else:
            # No grandchildren - handle tail appropriately
            if insert_position is not None and insert_position > 0:
                # Append to previous sibling's tail
                prev = parent[insert_position - 1]
                prev.tail = (prev.tail or "") + wrapper.tail
            else:
                # No previous sibling, append to parent's text
                parent.text = (parent.text or "") + wrapper.tail


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
            # If the child has its own children, unwrap it: move grandchildren up
            if len(child) > 0:
                # Only unwrap if there's no text content to preserve
                has_text = child.text is not None and child.text.strip() != ""

                if not has_text:
                    # Find where to insert grandchildren (at the child's position)
                    child_index = list(element).index(child)
                    # Unwrap the wrapper, inserting grandchildren at child's position
                    _unwrap_wrapper_element(element, child, insert_position=child_index)

                continue

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


def merge_consecutive_siblings(element: ET.Element) -> None:
    """Recursively merge consecutive sibling elements with identical attributes.

    This utility consolidates sequences of consecutive child elements that have
    the same tag and identical attributes by merging their text content. This is
    particularly useful for optimizing SVG <tspan> elements.

    Args:
        element: The XML element to process recursively.

    Example:
        Before: <text>
                    <tspan font-size="18" letter-spacing="0.72">す</tspan>
                    <tspan font-size="18" letter-spacing="0.72">だ</tspan>
                    <tspan font-size="18" letter-spacing="0.72">け</tspan>
                </text>

        After:  <text>
                    <tspan font-size="18" letter-spacing="0.72">すだけ</tspan>
                </text>

        Before: <text>
                    <tspan font-size="18" baseline-shift="-0.36" letter-spacing="0.72">さ</tspan>
                    <tspan font-size="18" letter-spacing="0.72">す</tspan>
                    <tspan font-size="18" letter-spacing="0.72">だ</tspan>
                </text>

        After:  <text>
                    <tspan font-size="18" baseline-shift="-0.36" letter-spacing="0.72">さ</tspan>
                    <tspan font-size="18" letter-spacing="0.72">すだ</tspan>
                </text>

    Note:
        - Only merges elements with the same tag name
        - Only merges elements with identical attribute sets
        - Preserves document order
        - Does not merge elements with child elements
        - Empty elements (no text or tail) are removed
    """
    # First, recursively process all children
    for child in list(element):
        merge_consecutive_siblings(child)

    # Then merge consecutive siblings with identical attributes
    children = list(element)
    if len(children) < 2:
        return

    i = 0
    while i < len(children):
        current = children[i]

        # Skip if current element has children (don't merge complex structures)
        if len(current) > 0:
            i += 1
            continue

        # Find consecutive siblings with same tag and attributes
        merge_group = [current]
        j = i + 1

        while j < len(children):
            next_elem = children[j]

            # Stop if next element has children
            if len(next_elem) > 0:
                break

            # Check if tags and attributes match
            if next_elem.tag == current.tag and next_elem.attrib == current.attrib:
                merge_group.append(next_elem)
                j += 1
            else:
                break

        # If we found consecutive siblings to merge (2 or more)
        if len(merge_group) >= 2:
            # Merge all text content into the first element
            merged_text = ""
            for elem in merge_group:
                if elem.text:
                    merged_text += elem.text

            # Set merged text to first element (or None if empty)
            merge_group[0].text = merged_text if merged_text else None

            # Preserve the tail of the last element in the group
            last_tail = merge_group[-1].tail

            # Remove all but the first element
            for elem in merge_group[1:]:
                element.remove(elem)

            # Set the tail to the first element
            merge_group[0].tail = last_tail

            # If the merged element is empty (no text, no tail), remove it
            if not merge_group[0].text and not merge_group[0].tail:
                element.remove(merge_group[0])

            # Update children list after removals
            children = list(element)
        else:
            i += 1


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

        Not merged (child has children):
        Before: <text><tspan><tspan>A</tspan><tspan>B</tspan></tspan></text>
        After:  <text><tspan><tspan>A</tspan><tspan>B</tspan></tspan></text>  (unchanged)
    """
    # First, recursively process all children
    for child in list(element):
        merge_singleton_children(child)

    # Merge singleton child if present (checking AFTER recursion)
    if len(element) == 1:
        child = element[0]

        # If the child has its own children, we can still optimize by "unwrapping" it:
        # move the grandchildren up to be direct children of element, removing the wrapper
        if len(child) > 0:
            # Only unwrap if there are no attribute conflicts and no text content to preserve
            has_conflict = (
                len(set(element.attrib.keys()) & set(child.attrib.keys())) > 0
            )
            has_text = child.text is not None and child.text.strip() != ""

            if not has_conflict and not has_text:
                # Move child's attributes to parent
                for key, value in child.attrib.items():
                    element.attrib[key] = value

                # Unwrap the wrapper, appending grandchildren to end
                _unwrap_wrapper_element(element, child, insert_position=None)

            return

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


def find_elements_with_font_family(
    svg: ET.Element, font_family: str
) -> list[ET.Element]:
    """Find all text/tspan elements that use the given font family.

    This function searches for text and tspan elements that have the specified
    font-family applied, either directly via attributes or through CSS inheritance
    from parent elements.

    Args:
        svg: SVG element tree to search.
        font_family: Font family name to search for (case-insensitive).

    Returns:
        List of text/tspan elements that use the specified font family.

    Note:
        - Searches both font-family attributes and style attributes
        - Supports CSS inheritance (walks up parent chain)
        - Case-insensitive font family matching
        - Only returns text and tspan elements (not their parents)

    Example:
        >>> svg = svg_utils.fromstring('<svg><text font-family="Arial">Hi</text></svg>')
        >>> elements = find_elements_with_font_family(svg, "Arial")
        >>> len(elements)
        1
    """
    matching_elements: list[ET.Element] = []
    font_family_lower = font_family.lower()

    # Build parent map for inheritance lookup
    parent_map = {c: p for p in svg.iter() for c in p}

    for element in svg.iter():
        # Get local tag name (strip namespace if present)
        tag = element.tag
        if "}" in tag:
            tag = tag.split("}", 1)[1]

        # Only process text/tspan elements
        if tag not in ("text", "tspan"):
            continue

        # Check if element uses target font (with inheritance)
        if _element_uses_font_family(element, parent_map, font_family_lower):
            matching_elements.append(element)

    return matching_elements


def _element_uses_font_family(
    element: ET.Element, parent_map: dict[ET.Element, ET.Element], target_font: str
) -> bool:
    """Check if element uses the target font (directly or through inheritance).

    Helper function for find_elements_with_font_family that walks up the parent
    chain to check for font-family declarations.

    Args:
        element: Element to check.
        parent_map: Dictionary mapping children to parents.
        target_font: Target font family name (lowercase).

    Returns:
        True if element uses the target font, False otherwise.
    """
    current = element
    while True:
        # Check direct font-family attribute
        elem_font_family = current.get("font-family")
        if elem_font_family:
            clean_family = elem_font_family.strip("'\"").split(",")[0].strip("'\"")
            return clean_family.lower() == target_font

        # Check style attribute for font-family
        style = current.get("style")
        if style and "font-family:" in style:
            match = re.search(r"font-family:\s*([^;]+)", style)
            if match:
                font_family_value = match.group(1).strip()
                families = [
                    f.strip().strip("'\"") for f in font_family_value.split(",")
                ]
                if families:
                    return families[0].lower() == target_font

        # Walk up to parent
        if current not in parent_map:
            break
        current = parent_map[current]

    return False


def extract_text_characters(element: ET.Element) -> str:
    """Extract text characters from an element for font subsetting.

    This function extracts both element.text and element.tail with HTML entity
    decoding. The tail is included because it's rendered using the element's
    font-family (not the parent's), which is important for accurate font subsetting.

    Control characters (newlines, tabs, etc.) are filtered out as they are not
    actually rendered in SVG text elements and should not be included in charset
    matching for font resolution.

    Args:
        element: XML element to extract text from (typically text or tspan).

    Returns:
        Text content (text + tail) with HTML entities decoded and control
        characters removed.

    Note:
        - Extracts element.text (content before first child element)
        - ALSO extracts tail (content after element's closing tag)
        - Does NOT include text from child elements
        - Decodes HTML/XML entities (e.g., &lt; → <, &#x4E00; → 一)
        - Filters out control characters (codepoints 0-31 except space)
        - Tail is included because SVG inherits font-family: the tail is rendered
          using the element's font, not the parent's font

    Example:
        >>> elem = ET.fromstring('<text>Hello &amp; world</text>')
        >>> extract_text_characters(elem)
        'Hello & world'

        >>> root = ET.fromstring('<text><tspan>A</tspan>B</text>')
        >>> tspan = root[0]
        >>> extract_text_characters(tspan)  # Returns 'AB' (text + tail)
        'AB'

        >>> elem = ET.fromstring('<text>Hello\\nWorld</text>')
        >>> extract_text_characters(elem)  # Newline filtered
        'HelloWorld'
    """
    import html

    result = ""
    if element.text:
        result += html.unescape(element.text)
    if element.tail:
        result += html.unescape(element.tail)

    # Filter out control characters (C0: 0-31, DEL: 127, C1: 128-159)
    # These are not rendered in SVG text and cause incorrect font matching
    # (e.g., newline causes Arial to be substituted with LastResort on macOS)
    result = "".join(
        char for char in result if ord(char) >= 32 and not (127 <= ord(char) <= 159)
    )

    return result


def add_font_family(
    element: ET.Element, original_family: str, fallback_family: str
) -> None:
    """Add fallback font to font-family in the given element.

    This function modifies an SVG text/tspan element by appending a fallback font family
    to its existing font-family specification. It handles both font-family attributes
    and font-family declarations within style attributes.

    Args:
        element: Element to update (typically text or tspan element).
        original_family: Original font family name to match.
        fallback_family: Fallback font family name to append.

    Example:
        Before: <text font-family="Arial">Hello</text>
        After:  <text font-family="'Arial', 'Helvetica'">Hello</text>

        Before: <tspan style="font-family: Arial">Hello</tspan>
        After:  <tspan style="font-family: 'Arial', 'Helvetica'">Hello</tspan>

    Note:
        - Only updates element if font-family exactly matches original_family
        - Updates both font-family attributes and style attributes
        - Quotes font family names in the output for CSS compliance
    """
    # Check font-family attribute
    font_family = element.get("font-family")
    if font_family:
        # Add fallback chain
        clean_family = font_family.strip("'\"")
        if clean_family == original_family:
            element.set("font-family", f"'{original_family}', '{fallback_family}'")

    # Check style attribute for font-family
    style = element.get("style")
    if style and "font-family:" in style:

        def replace_font_family(match: re.Match[str]) -> str:
            font_family_value = match.group(1).strip()
            # Parse the first font (requested font)
            families = [f.strip().strip("'\"") for f in font_family_value.split(",")]
            if families and families[0] == original_family:
                # Build fallback chain
                return f"font-family: '{original_family}', '{fallback_family}'"
            return match.group(0)

        # Replace font-family in style attribute
        updated_style = re.sub(r"font-family:\s*([^;]+)", replace_font_family, style)
        if updated_style != style:
            element.set("style", updated_style)


def insert_or_update_style_element(svg: ET.Element, css_content: str) -> None:
    """Insert or update a <style> element in the SVG root.

    Args:
        svg: SVG root element to modify.
        css_content: CSS content to insert or append.

    Note:
        - If a <style> element exists as first child, appends to it
        - Otherwise creates a new <style> element as first child
        - Idempotent: skips if CSS content already present
    """
    # Find existing <style> element (check first child only)
    style_element = None
    if len(svg) > 0:
        first_child = svg[0]
        # Check if it's a style element (handle namespaced tags)
        tag = first_child.tag
        local_name = tag.split("}")[-1] if "}" in tag else tag
        if local_name == "style":
            style_element = first_child

    if style_element is not None:
        # Update existing style element
        existing_text = style_element.text or ""
        # Check if our fonts are already embedded (idempotent check)
        if css_content in existing_text:
            logger.debug("CSS content already present, skipping")
            return
        # Append to existing styles
        style_element.text = existing_text + "\n" + css_content
    else:
        # Create new style element as first child
        style_element = ET.Element("style")
        style_element.text = css_content
        svg.insert(0, style_element)
