"""Font subsetting utilities for reducing embedded font file sizes."""

import html
import logging
import re
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Check for fonttools availability
try:
    from fontTools import subset
    from fontTools.ttLib import TTFont

    HAS_FONTTOOLS = True
except ImportError:
    HAS_FONTTOOLS = False


def extract_used_unicode(svg_tree: ET.Element) -> dict[str, set[str]]:
    """Extract Unicode characters per font-family from SVG text elements.

    This function analyzes all <text> and <tspan> elements in the SVG tree
    to determine which Unicode characters are used by each font family.

    Args:
        svg_tree: Root SVG element to analyze.

    Returns:
        Dictionary mapping font-family names to sets of Unicode characters.
        Example: {"Arial": {"A", "B", "C"}, "Noto Sans JP": {"あ", "い"}}

    Note:
        - Handles nested <tspan> elements
        - Decodes XML entities (e.g., &lt;, &#x4E00;)
        - Extracts font-family from style attributes
        - Returns empty dict if no text elements found
    """
    font_usage: dict[str, set[str]] = {}

    # Build parent map for inheritance lookup
    parent_map = {c: p for p in svg_tree.iter() for c in p}

    # Find all text and tspan elements
    for element in svg_tree.iter():
        tag_name = _get_local_tag_name(element)
        if tag_name not in ("text", "tspan"):
            continue

        # Extract font-family from element or parent
        font_family = _extract_font_family_with_inheritance(element, parent_map)
        if not font_family:
            continue

        # Extract text content for this element only (not children)
        text_content = _extract_direct_text_content(element)
        if not text_content:
            continue

        # Add characters to the set for this font
        if font_family not in font_usage:
            font_usage[font_family] = set()

        font_usage[font_family].update(text_content)

    logger.debug(
        f"Extracted Unicode usage: {len(font_usage)} font(s), "
        f"{sum(len(chars) for chars in font_usage.values())} unique char(s) total"
    )

    return font_usage


def subset_font(
    input_path: str,
    output_format: str,
    unicode_chars: set[str],
) -> bytes:
    """Subset a font file to include only specified Unicode characters.

    This function uses fontTools (pyftsubset) to create a minimal font file
    containing only the glyphs needed for the specified characters.

    Args:
        input_path: Path to input font file (TTF/OTF).
        output_format: Output format - "ttf", "otf", or "woff2".
        unicode_chars: Set of Unicode characters to include in the subset.

    Returns:
        Subset font file as bytes.

    Raises:
        ImportError: If fonttools package is not installed.
        ValueError: If output_format is unsupported.
        Exception: If subsetting fails (invalid font, I/O error, etc.).

    Example:
        >>> chars = {"A", "B", "C", "あ"}
        >>> font_bytes = subset_font("/usr/share/fonts/arial.ttf", "woff2", chars)
        >>> len(font_bytes)  # Much smaller than original
        8432
    """
    if not HAS_FONTTOOLS:
        raise ImportError(
            "Font subsetting requires the fonttools package. "
            "Install with: uv sync --group fonts"
        )

    if output_format not in ("ttf", "otf", "woff2"):
        raise ValueError(
            f"Unsupported font format: {output_format}. "
            f"Supported formats: ttf, otf, woff2"
        )

    if not unicode_chars:
        logger.warning("No Unicode characters provided for subsetting, using all glyphs")

    # Convert characters to Unicode code points
    unicodes = _chars_to_unicode_list(unicode_chars)

    logger.debug(
        f"Subsetting font: {input_path} -> {output_format} "
        f"({len(unicode_chars)} char(s), {len(unicodes)} codepoint(s))"
    )

    try:
        # Load the font
        font = TTFont(input_path)

        # Create subsetter with options
        subsetter = subset.Subsetter()

        # Subset options
        options = subset.Options()
        options.drop_tables = []  # Keep all tables by default
        options.layout_features = ["*"]  # Preserve all OpenType features
        options.name_IDs = ["*"]  # Preserve all name table entries
        options.name_languages = ["*"]  # Preserve all languages
        options.notdef_outline = True  # Keep .notdef glyph
        options.glyph_names = True  # Preserve glyph names (helps debugging)

        subsetter.options = options

        # Populate subset with Unicode characters
        if unicodes:
            subsetter.populate(unicodes=unicodes)
        else:
            # If no characters specified, include all glyphs
            subsetter.populate(glyphs=font.getGlyphOrder())

        # Perform subsetting
        subsetter.subset(font)

        # Save to bytes (using a temporary in-memory approach)
        import io

        output_buffer = io.BytesIO()

        # Set flavor for WOFF2 on the font object before saving
        if output_format == "woff2":
            font.flavor = "woff2"

        font.save(output_buffer)
        font_bytes = output_buffer.getvalue()

        logger.debug(
            f"Subsetting complete: {len(font_bytes)} bytes "
            f"(~{len(font_bytes) / 1024:.1f} KB)"
        )

        return font_bytes

    except Exception as e:
        logger.error(f"Font subsetting failed for {input_path}: {e}")
        raise


def _get_local_tag_name(element: ET.Element) -> str:
    """Extract local tag name from element (handles namespaces).

    Args:
        element: XML element.

    Returns:
        Local tag name without namespace prefix.

    Example:
        >>> elem.tag = "{http://www.w3.org/2000/svg}text"
        >>> _get_local_tag_name(elem)
        "text"
    """
    tag = element.tag
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _extract_font_family(element: ET.Element) -> str | None:
    """Extract font-family from element's style or font-family attribute.

    Args:
        element: XML element (text or tspan).

    Returns:
        Font family name, or None if not found.

    Example:
        >>> _extract_font_family(<text style="font-family: Arial; ...">)
        "Arial"
    """
    # Try style attribute first
    style = element.get("style", "")
    if style:
        match = re.search(r"font-family:\s*([^;]+)", style)
        if match:
            font_family = match.group(1).strip()
            # Remove quotes if present
            font_family = font_family.strip("'\"")
            return font_family

    # Try direct font-family attribute
    font_family = element.get("font-family")
    if font_family:
        return font_family.strip("'\"")

    return None


def _extract_font_family_with_inheritance(
    element: ET.Element, parent_map: dict[ET.Element, ET.Element]
) -> str | None:
    """Extract font-family from element or inherited from parent.

    Walks up the element tree to find the first font-family declaration.
    This handles cases where <tspan> elements inherit font-family from
    their parent <text> element.

    Args:
        element: XML element (text or tspan).
        parent_map: Dictionary mapping child elements to their parents.

    Returns:
        Font family name, or None if not found in element or ancestors.

    Example:
        >>> <text font-family="Arial"><tspan>Hello</tspan></text>
        >>> _extract_font_family_with_inheritance(tspan_element, parent_map)
        "Arial"
    """
    # Try current element first
    font_family = _extract_font_family(element)
    if font_family:
        return font_family

    # Walk up parent tree to find inherited font-family
    current = element
    while current in parent_map:
        current = parent_map[current]
        font_family = _extract_font_family(current)
        if font_family:
            return font_family

    return None


def _extract_text_content(element: ET.Element) -> str:
    """Extract and decode all text content from element (including entities).

    Args:
        element: XML element.

    Returns:
        Decoded text content with XML entities resolved.

    Note:
        - Handles numeric character references (&#x4E00;, &#20013;)
        - Handles named entities (&lt;, &gt;, &amp;, etc.)
        - Recursively includes text from child elements
    """
    # Collect all text (element.text and tail from all descendants)
    text_parts = []

    if element.text:
        text_parts.append(element.text)

    for child in element:
        # Recursively get text from children
        child_text = _extract_text_content(child)
        if child_text:
            text_parts.append(child_text)
        # Also include tail text (text after child element)
        if child.tail:
            text_parts.append(child.tail)

    raw_text = "".join(text_parts)

    # Decode HTML/XML entities
    decoded_text = html.unescape(raw_text)

    return decoded_text


def _extract_direct_text_content(element: ET.Element) -> str:
    """Extract text content directly owned by this element (not children).

    This function extracts only the text that belongs to the current element,
    not text from child elements. This is important for font subsetting because
    child elements may have different font-family attributes.

    Args:
        element: XML element.

    Returns:
        Decoded text content (only element.text, not children).

    Example:
        <text>Hello<tspan>World</tspan></text>
        Returns: "Hello" (not "HelloWorld")
    """
    if element.text:
        # Decode HTML/XML entities
        return html.unescape(element.text)
    return ""


def _chars_to_unicode_list(chars: set[str]) -> list[int]:
    """Convert set of characters to list of Unicode code points.

    Args:
        chars: Set of Unicode characters (e.g., {"A", "あ", "中"}).

    Returns:
        List of Unicode code points (e.g., [0x41, 0x3042, 0x4E2D]).

    Note:
        - Handles multi-codepoint characters (emoji, combining marks)
        - Returns unique code points sorted for deterministic output
    """
    codepoints = set()

    for char in chars:
        # Each character may contain multiple code points (e.g., emoji with modifiers)
        for code_point in char:
            codepoints.add(ord(code_point))

    return sorted(codepoints)
