"""Tests for SVG optimization features."""

import xml.etree.ElementTree as ET

from psd2svg import svg_utils


def get_local_tag(element: ET.Element) -> str:
    """Get local tag name without namespace."""
    tag = element.tag
    return tag.split("}")[-1] if "}" in tag else tag


class TestConsolidateDefs:
    """Tests for consolidate_defs optimization."""

    def test_consolidate_single_defs(self) -> None:
        """Test consolidating a single <defs> element."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect fill="url(#g1)"/>
            <defs>
                <linearGradient id="g1"/>
            </defs>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have one <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Should contain the gradient
        assert len(svg[0]) == 1
        assert get_local_tag(svg[0][0]) == "linearGradient"
        assert svg[0][0].get("id") == "g1"
        # Rect should be second child
        assert get_local_tag(svg[1]) == "rect"

    def test_consolidate_multiple_defs(self) -> None:
        """Test consolidating multiple <defs> elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1"/>
            </defs>
            <rect fill="url(#g1)"/>
            <defs>
                <filter id="f1"/>
            </defs>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have one <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Should contain both elements
        assert len(svg[0]) == 2
        assert get_local_tag(svg[0][0]) == "linearGradient"
        assert get_local_tag(svg[0][1]) == "filter"
        # Only one defs element total
        defs_count = sum(1 for child in svg if get_local_tag(child) == "defs")
        assert defs_count == 1

    def test_consolidate_nested_defs(self) -> None:
        """Test consolidating nested <defs> within groups."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <defs>
                    <linearGradient id="g1"/>
                </defs>
                <rect fill="url(#g1)"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have global <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        assert len(svg[0]) == 1
        assert get_local_tag(svg[0][0]) == "linearGradient"
        # Group should no longer contain defs
        group = svg[1]
        assert get_local_tag(group) == "g"
        assert len(group) == 1
        assert get_local_tag(group[0]) == "rect"

    def test_consolidate_inline_filters(self) -> None:
        """Test consolidating inline <filter> elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect filter="url(#f1)"/>
            <filter id="f1">
                <feGaussianBlur stdDeviation="2"/>
            </filter>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Filter should be inside defs
        assert len(svg[0]) == 1
        assert get_local_tag(svg[0][0]) == "filter"
        assert svg[0][0].get("id") == "f1"
        # Filter's children should be preserved
        assert len(svg[0][0]) == 1
        assert get_local_tag(svg[0][0][0]) == "feGaussianBlur"

    def test_consolidate_inline_gradients(self) -> None:
        """Test consolidating inline gradient elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect fill="url(#g1)"/>
            <linearGradient id="g1">
                <stop offset="0%" stop-color="#fff"/>
                <stop offset="100%" stop-color="#000"/>
            </linearGradient>
            <circle fill="url(#g2)"/>
            <radialGradient id="g2">
                <stop offset="0%" stop-color="#f00"/>
            </radialGradient>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Should contain both gradients
        assert len(svg[0]) == 2
        assert get_local_tag(svg[0][0]) == "linearGradient"
        assert svg[0][0].get("id") == "g1"
        assert get_local_tag(svg[0][1]) == "radialGradient"
        assert svg[0][1].get("id") == "g2"
        # Gradient children should be preserved
        assert len(svg[0][0]) == 2  # Two stops
        assert len(svg[0][1]) == 1  # One stop

    def test_consolidate_patterns(self) -> None:
        """Test consolidating <pattern> elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect fill="url(#p1)"/>
            <pattern id="p1">
                <circle cx="5" cy="5" r="5"/>
            </pattern>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Pattern should be inside defs
        assert len(svg[0]) == 1
        assert get_local_tag(svg[0][0]) == "pattern"
        assert svg[0][0].get("id") == "p1"

    def test_consolidate_clip_paths(self) -> None:
        """Test consolidating <clipPath> elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect clip-path="url(#c1)"/>
            <clipPath id="c1">
                <circle cx="50" cy="50" r="50"/>
            </clipPath>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # ClipPath should be inside defs
        assert len(svg[0]) == 1
        assert get_local_tag(svg[0][0]) == "clipPath"
        assert svg[0][0].get("id") == "c1"

    def test_consolidate_markers(self) -> None:
        """Test consolidating <marker> elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <line marker-end="url(#arrow)"/>
            <marker id="arrow">
                <path d="M 0 0 L 10 5 L 0 10 z"/>
            </marker>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Marker should be inside defs
        assert len(svg[0]) == 1
        assert get_local_tag(svg[0][0]) == "marker"
        assert svg[0][0].get("id") == "arrow"

    def test_consolidate_symbols(self) -> None:
        """Test consolidating <symbol> elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <use href="#icon"/>
            <symbol id="icon">
                <circle cx="5" cy="5" r="5"/>
            </symbol>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Symbol should be inside defs
        assert len(svg[0]) == 1
        assert get_local_tag(svg[0][0]) == "symbol"
        assert svg[0][0].get("id") == "icon"

    def test_consolidate_mixed_definitions(self) -> None:
        """Test consolidating mixed definition types."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <filter id="f1"/>
            <rect fill="url(#g1)" filter="url(#f1)"/>
            <linearGradient id="g1"/>
            <defs>
                <pattern id="p1"/>
            </defs>
            <clipPath id="c1"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Should contain all 4 definitions
        assert len(svg[0]) == 4
        ids = {child.get("id") for child in svg[0]}
        assert ids == {"f1", "g1", "p1", "c1"}
        # Rect should be second child
        assert get_local_tag(svg[1]) == "rect"

    def test_consolidate_preserves_order(self) -> None:
        """Test that consolidation preserves definition order."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <linearGradient id="g1"/>
            <filter id="f1"/>
            <pattern id="p1"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Order should be preserved
        assert svg[0][0].get("id") == "g1"
        assert svg[0][1].get("id") == "f1"
        assert svg[0][2].get("id") == "p1"

    def test_consolidate_empty_svg(self) -> None:
        """Test consolidating an SVG with no definitions."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="100" height="100"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should not create empty <defs>
        assert get_local_tag(svg[0]) == "rect"
        defs_count = sum(1 for child in svg if get_local_tag(child) == "defs")
        assert defs_count == 0

    def test_consolidate_removes_empty_defs(self) -> None:
        """Test that empty <defs> elements are removed."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs></defs>
            <rect x="0" y="0" width="100" height="100"/>
            <defs></defs>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should not have any <defs>
        defs_count = sum(1 for child in svg if get_local_tag(child) == "defs")
        assert defs_count == 0
        # Should still have rect
        assert get_local_tag(svg[0]) == "rect"

    def test_consolidate_with_existing_global_defs(self) -> None:
        """Test consolidating when a global <defs> already exists."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1"/>
            </defs>
            <filter id="f1"/>
            <rect/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have one <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Should contain both elements
        assert len(svg[0]) == 2
        assert svg[0][0].get("id") == "g1"
        assert svg[0][1].get("id") == "f1"

    def test_consolidate_deeply_nested(self) -> None:
        """Test consolidating definitions nested deep in the tree."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <g>
                    <g>
                        <filter id="f1"/>
                        <rect filter="url(#f1)"/>
                    </g>
                </g>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        assert len(svg[0]) == 1
        assert svg[0][0].get("id") == "f1"
        # Filter should be removed from nested location
        innermost_g = svg[1][0][0]
        assert len(innermost_g) == 1
        assert get_local_tag(innermost_g[0]) == "rect"

    def test_consolidate_does_not_move_masks(self) -> None:
        """Test that <mask> elements are NOT moved (they can contain rendered content)."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect mask="url(#m1)"/>
            <mask id="m1">
                <rect fill="white"/>
            </mask>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Mask should NOT be moved to defs
        # If there are no other definitions, defs shouldn't be created
        if svg[0].tag == "defs":
            assert len(svg[0]) == 0  # Defs should be empty
        # Mask should still be at top level
        mask_found = False
        for child in svg:
            if get_local_tag(child) == "mask":
                mask_found = True
                break
        assert mask_found

    def test_consolidate_complex_real_world_example(self) -> None:
        """Test consolidating a complex real-world-like SVG."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <image filter="url(#coloroverlay)"/>
            <filter id="coloroverlay">
                <feFlood flood-color="#ff0000"/>
                <feComposite operator="in" in2="SourceAlpha"/>
            </filter>
            <mask id="mask">
                <defs>
                    <image id="image_2"/>
                </defs>
                <use href="#image_2"/>
                <filter id="stroke">
                    <feMorphology operator="erode" radius="1"/>
                    <feComposite operator="xor" in2="SourceAlpha"/>
                </filter>
                <use href="#image_2" filter="url(#stroke)"/>
            </mask>
            <linearGradient id="gradient">
                <stop offset="0%" stop-color="#fff"/>
            </linearGradient>
            <use href="#image_2"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.consolidate_defs(svg)

        # Should have <defs> as first child
        assert get_local_tag(svg[0]) == "defs"
        # Should contain: coloroverlay filter, image_2, stroke filter, gradient
        assert len(svg[0]) == 4
        ids = {child.get("id") for child in svg[0]}
        assert ids == {"coloroverlay", "image_2", "stroke", "gradient"}
        # Mask should still exist but its nested defs should be gone
        mask = None
        for child in svg:
            if get_local_tag(child) == "mask":
                mask = child
                break
        assert mask is not None
        # Mask should not contain any defs elements
        mask_defs = [child for child in mask if get_local_tag(child) == "defs"]
        assert len(mask_defs) == 0
