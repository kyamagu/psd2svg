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


class TestDeduplicateDefinitions:
    """Tests for deduplicate_definitions optimization."""

    def test_deduplicate_identical_linear_gradients(self) -> None:
        """Test merging two identical linearGradient elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1">
                    <stop offset="0%" stop-color="red"/>
                    <stop offset="100%" stop-color="blue"/>
                </linearGradient>
                <linearGradient id="g2">
                    <stop offset="0%" stop-color="red"/>
                    <stop offset="100%" stop-color="blue"/>
                </linearGradient>
            </defs>
            <rect fill="url(#g1)"/>
            <circle fill="url(#g2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only one gradient
        defs = svg[0]
        assert len(defs) == 1
        assert get_local_tag(defs[0]) == "linearGradient"
        assert defs[0].get("id") == "g1"  # First occurrence kept

        # Both elements should reference g1
        rect = svg[1]
        circle = svg[2]
        assert rect.get("fill") == "url(#g1)"
        assert circle.get("fill") == "url(#g1)"

    def test_deduplicate_identical_radial_gradients(self) -> None:
        """Test merging two identical radialGradient elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="rg1" cx="50%" cy="50%">
                    <stop offset="0%" stop-color="white"/>
                    <stop offset="100%" stop-color="black"/>
                </radialGradient>
                <radialGradient id="rg2" cx="50%" cy="50%">
                    <stop offset="0%" stop-color="white"/>
                    <stop offset="100%" stop-color="black"/>
                </radialGradient>
            </defs>
            <ellipse fill="url(#rg1)"/>
            <circle fill="url(#rg2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only one gradient
        defs = svg[0]
        assert len(defs) == 1
        assert get_local_tag(defs[0]) == "radialGradient"
        assert defs[0].get("id") == "rg1"

        # Both elements should reference rg1
        ellipse = svg[1]
        circle = svg[2]
        assert ellipse.get("fill") == "url(#rg1)"
        assert circle.get("fill") == "url(#rg1)"

    def test_deduplicate_identical_filters(self) -> None:
        """Test merging two identical filter elements with children."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <filter id="f1">
                    <feGaussianBlur stdDeviation="2"/>
                </filter>
                <filter id="f2">
                    <feGaussianBlur stdDeviation="2"/>
                </filter>
            </defs>
            <rect filter="url(#f1)"/>
            <circle filter="url(#f2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only one filter
        defs = svg[0]
        assert len(defs) == 1
        assert get_local_tag(defs[0]) == "filter"
        assert defs[0].get("id") == "f1"

        # Both elements should reference f1
        rect = svg[1]
        circle = svg[2]
        assert rect.get("filter") == "url(#f1)"
        assert circle.get("filter") == "url(#f1)"

    def test_deduplicate_identical_patterns(self) -> None:
        """Test merging two identical pattern elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <pattern id="p1" width="10" height="10">
                    <circle cx="5" cy="5" r="3"/>
                </pattern>
                <pattern id="p2" width="10" height="10">
                    <circle cx="5" cy="5" r="3"/>
                </pattern>
            </defs>
            <rect fill="url(#p1)"/>
            <path fill="url(#p2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only one pattern
        defs = svg[0]
        assert len(defs) == 1
        assert get_local_tag(defs[0]) == "pattern"
        assert defs[0].get("id") == "p1"

        # Both elements should reference p1
        rect = svg[1]
        path = svg[2]
        assert rect.get("fill") == "url(#p1)"
        assert path.get("fill") == "url(#p1)"

    def test_deduplicate_clippath_marker_symbol(self) -> None:
        """Test merging less common types (clipPath, marker, symbol)."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <clipPath id="c1">
                    <circle cx="50" cy="50" r="40"/>
                </clipPath>
                <clipPath id="c2">
                    <circle cx="50" cy="50" r="40"/>
                </clipPath>
            </defs>
            <rect clip-path="url(#c1)"/>
            <circle clip-path="url(#c2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only one clipPath
        defs = svg[0]
        assert len(defs) == 1
        assert get_local_tag(defs[0]) == "clipPath"
        assert defs[0].get("id") == "c1"

        # Both elements should reference c1
        rect = svg[1]
        circle = svg[2]
        assert rect.get("clip-path") == "url(#c1)"
        assert circle.get("clip-path") == "url(#c1)"

    def test_deduplicate_mixed_types(self) -> None:
        """Test merging multiple types at once."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1">
                    <stop offset="0%" stop-color="red"/>
                </linearGradient>
                <filter id="f1">
                    <feGaussianBlur stdDeviation="2"/>
                </filter>
                <linearGradient id="g2">
                    <stop offset="0%" stop-color="red"/>
                </linearGradient>
                <filter id="f2">
                    <feGaussianBlur stdDeviation="2"/>
                </filter>
            </defs>
            <rect fill="url(#g1)" filter="url(#f1)"/>
            <circle fill="url(#g2)" filter="url(#f2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only two elements (one gradient, one filter)
        defs = svg[0]
        assert len(defs) == 2
        assert defs[0].get("id") == "g1"
        assert defs[1].get("id") == "f1"

        # Both elements should reference g1 and f1
        rect = svg[1]
        circle = svg[2]
        assert rect.get("fill") == "url(#g1)"
        assert rect.get("filter") == "url(#f1)"
        assert circle.get("fill") == "url(#g1)"
        assert circle.get("filter") == "url(#f1)"

    def test_update_fill_references(self) -> None:
        """Test updating fill='url(#id)' references."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1"><stop offset="0%"/></linearGradient>
                <linearGradient id="g2"><stop offset="0%"/></linearGradient>
            </defs>
            <rect fill="url(#g2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        rect = svg[1]
        assert rect.get("fill") == "url(#g1)"

    def test_update_stroke_references(self) -> None:
        """Test updating stroke='url(#id)' references."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1"><stop offset="0%"/></linearGradient>
                <linearGradient id="g2"><stop offset="0%"/></linearGradient>
            </defs>
            <line stroke="url(#g2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        line = svg[1]
        assert line.get("stroke") == "url(#g1)"

    def test_update_filter_references(self) -> None:
        """Test updating filter='url(#id)' references."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <filter id="f1"><feGaussianBlur stdDeviation="2"/></filter>
                <filter id="f2"><feGaussianBlur stdDeviation="2"/></filter>
            </defs>
            <rect filter="url(#f2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        rect = svg[1]
        assert rect.get("filter") == "url(#f1)"

    def test_update_clippath_references(self) -> None:
        """Test updating clip-path='url(#id)' references."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <clipPath id="c1"><circle cx="50" cy="50" r="40"/></clipPath>
                <clipPath id="c2"><circle cx="50" cy="50" r="40"/></clipPath>
            </defs>
            <rect clip-path="url(#c2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        rect = svg[1]
        assert rect.get("clip-path") == "url(#c1)"

    def test_update_marker_references(self) -> None:
        """Test updating marker-start/mid/end='url(#id)' references."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <marker id="m1"><circle cx="5" cy="5" r="2"/></marker>
                <marker id="m2"><circle cx="5" cy="5" r="2"/></marker>
            </defs>
            <path marker-start="url(#m2)" marker-mid="url(#m2)" marker-end="url(#m2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        path = svg[1]
        assert path.get("marker-start") == "url(#m1)"
        assert path.get("marker-mid") == "url(#m1)"
        assert path.get("marker-end") == "url(#m1)"

    def test_multiple_references_to_same_id(self) -> None:
        """Test same duplicate referenced multiple times."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1"><stop offset="0%"/></linearGradient>
                <linearGradient id="g2"><stop offset="0%"/></linearGradient>
            </defs>
            <rect fill="url(#g2)"/>
            <circle fill="url(#g2)"/>
            <ellipse fill="url(#g2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # All three should reference g1
        rect = svg[1]
        circle = svg[2]
        ellipse = svg[3]
        assert rect.get("fill") == "url(#g1)"
        assert circle.get("fill") == "url(#g1)"
        assert ellipse.get("fill") == "url(#g1)"

    def test_attribute_order_independence(self) -> None:
        """Test elements identical except attribute order."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="red"/>
                </linearGradient>
                <linearGradient id="g2" y2="0%" x2="100%" y1="0%" x1="0%">
                    <stop offset="0%" stop-color="red"/>
                </linearGradient>
            </defs>
            <rect fill="url(#g2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only one gradient (attribute order normalized)
        defs = svg[0]
        assert len(defs) == 1
        assert defs[0].get("id") == "g1"

        # Reference should be updated
        rect = svg[1]
        assert rect.get("fill") == "url(#g1)"

    def test_no_duplicates(self) -> None:
        """Test all elements unique (no changes)."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1">
                    <stop offset="0%" stop-color="red"/>
                </linearGradient>
                <linearGradient id="g2">
                    <stop offset="0%" stop-color="blue"/>
                </linearGradient>
            </defs>
            <rect fill="url(#g1)"/>
            <circle fill="url(#g2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should still have two gradients
        defs = svg[0]
        assert len(defs) == 2
        assert defs[0].get("id") == "g1"
        assert defs[1].get("id") == "g2"

        # References unchanged
        rect = svg[1]
        circle = svg[2]
        assert rect.get("fill") == "url(#g1)"
        assert circle.get("fill") == "url(#g2)"

    def test_empty_defs(self) -> None:
        """Test no definition elements (no changes)."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs/>
            <rect fill="red"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should still have empty defs
        defs = svg[0]
        assert get_local_tag(defs) == "defs"
        assert len(defs) == 0

    def test_partial_duplicates(self) -> None:
        """Test mix of unique and duplicate elements."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g1"><stop offset="0%"/></linearGradient>
                <linearGradient id="g2"><stop offset="50%"/></linearGradient>
                <linearGradient id="g3"><stop offset="0%"/></linearGradient>
            </defs>
            <rect fill="url(#g1)"/>
            <circle fill="url(#g2)"/>
            <ellipse fill="url(#g3)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have two gradients (g1 and g2)
        defs = svg[0]
        assert len(defs) == 2
        assert defs[0].get("id") == "g1"
        assert defs[1].get("id") == "g2"

        # g3 reference updated to g1
        rect = svg[1]
        circle = svg[2]
        ellipse = svg[3]
        assert rect.get("fill") == "url(#g1)"
        assert circle.get("fill") == "url(#g2)"
        assert ellipse.get("fill") == "url(#g1)"  # Updated

    def test_nested_filter_elements(self) -> None:
        """Test complex filters with nested children."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <filter id="f1">
                    <feGaussianBlur stdDeviation="2"/>
                    <feOffset dx="3" dy="3"/>
                </filter>
                <filter id="f2">
                    <feGaussianBlur stdDeviation="2"/>
                    <feOffset dx="3" dy="3"/>
                </filter>
            </defs>
            <rect filter="url(#f1)"/>
            <circle filter="url(#f2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only one filter
        defs = svg[0]
        assert len(defs) == 1
        assert defs[0].get("id") == "f1"

        # Both should reference f1
        rect = svg[1]
        circle = svg[2]
        assert rect.get("filter") == "url(#f1)"
        assert circle.get("filter") == "url(#f1)"

    def test_first_occurrence_kept(self) -> None:
        """Test first occurrence is canonical, others removed."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="gradient"><stop offset="0%"/></linearGradient>
                <linearGradient id="gradient_2"><stop offset="0%"/></linearGradient>
                <linearGradient id="gradient_3"><stop offset="0%"/></linearGradient>
            </defs>
            <rect fill="url(#gradient)"/>
            <circle fill="url(#gradient_2)"/>
            <ellipse fill="url(#gradient_3)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.deduplicate_definitions(svg)

        # Should have only one gradient with id="gradient"
        defs = svg[0]
        assert len(defs) == 1
        assert defs[0].get("id") == "gradient"

        # All should reference "gradient"
        rect = svg[1]
        circle = svg[2]
        ellipse = svg[3]
        assert rect.get("fill") == "url(#gradient)"
        assert circle.get("fill") == "url(#gradient)"
        assert ellipse.get("fill") == "url(#gradient)"

    def test_integration_with_consolidate_defs(self) -> None:
        """Test pipeline: consolidate → deduplicate."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect fill="url(#g1)"/>
            <linearGradient id="g1"><stop offset="0%"/></linearGradient>
            <defs>
                <linearGradient id="g2"><stop offset="0%"/></linearGradient>
            </defs>
            <circle fill="url(#g2)"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)

        # Apply both optimizations
        svg_utils.consolidate_defs(svg)
        svg_utils.deduplicate_definitions(svg)

        # Should have global defs as first child
        assert get_local_tag(svg[0]) == "defs"
        # Should have only one gradient after deduplication
        assert len(svg[0]) == 1
        # Note: consolidate_defs processes defs content first, then inline elements
        # So g2 (from defs) becomes first occurrence and is kept
        canonical_id = svg[0][0].get("id")
        assert canonical_id in ("g1", "g2")  # Either is valid after consolidation

        # All references should point to the same canonical ID
        rect = svg[1]
        circle = svg[2]
        assert rect.get("fill") == f"url(#{canonical_id})"
        assert circle.get("fill") == f"url(#{canonical_id})"


class TestUnwrapGroups:
    """Tests for unwrap_groups optimization."""

    def test_unwrap_simple_group(self) -> None:
        """Test unwrapping a simple group with no attributes."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group should be unwrapped, rect moved to svg level
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "rect"
        # Verify all attributes are preserved
        assert svg[0].get("x") == "0"
        assert svg[0].get("y") == "0"
        assert svg[0].get("width") == "100"
        assert svg[0].get("height") == "100"

    def test_preserve_group_with_opacity(self) -> None:
        """Test that groups with opacity are NOT unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g opacity="0.5">
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group should be preserved
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "g"
        assert svg[0].get("opacity") == "0.5"
        assert len(svg[0]) == 1
        assert get_local_tag(svg[0][0]) == "rect"

    def test_preserve_group_with_style(self) -> None:
        """Test that groups with style are NOT unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g style="isolation: isolate">
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group should be preserved
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "g"
        assert "isolation" in svg[0].get("style", "")
        assert len(svg[0]) == 1

    def test_preserve_group_with_mask(self) -> None:
        """Test that groups with mask are NOT unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g mask="url(#m1)">
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group should be preserved
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "g"
        assert svg[0].get("mask") == "url(#m1)"

    def test_preserve_group_with_clip_path(self) -> None:
        """Test that groups with clip-path are NOT unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g clip-path="url(#c1)">
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group should be preserved
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "g"
        assert svg[0].get("clip-path") == "url(#c1)"

    def test_preserve_group_with_filter(self) -> None:
        """Test that groups with filter are NOT unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g filter="url(#f1)">
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group should be preserved
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "g"
        assert svg[0].get("filter") == "url(#f1)"

    def test_preserve_group_with_id(self) -> None:
        """Test that groups with id are NOT unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g id="group1">
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group should be preserved (may be referenced)
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "g"
        assert svg[0].get("id") == "group1"

    def test_preserve_group_with_title_child(self) -> None:
        """Test that groups with <title> children are NOT unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <title>Label</title>
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group should be preserved to avoid <title> conflicts
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "g"
        assert len(svg[0]) == 2
        assert get_local_tag(svg[0][0]) == "title"

    def test_unwrap_nested_groups(self) -> None:
        """Test unwrapping multiple levels of nested groups."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <g>
                    <g>
                        <rect x="0" y="0" width="100" height="100"/>
                    </g>
                </g>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # All nested groups should be unwrapped
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "rect"

    def test_remove_empty_groups(self) -> None:
        """Test that empty groups are removed entirely."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g></g>
            <rect x="0" y="0" width="100" height="100"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Empty group should be removed
        assert len(svg) == 1
        assert get_local_tag(svg[0]) == "rect"

    def test_unwrap_groups_in_defs(self) -> None:
        """Test that groups inside <defs> are unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <g>
                    <linearGradient id="g1"/>
                </g>
            </defs>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Group inside defs should be unwrapped
        defs = svg[0]
        assert get_local_tag(defs) == "defs"
        assert len(defs) == 1
        assert get_local_tag(defs[0]) == "linearGradient"

    def test_unwrap_group_with_multiple_children(self) -> None:
        """Test unwrapping preserves order of multiple children."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <rect x="0" y="0" width="100" height="100"/>
                <circle cx="50" cy="50" r="25"/>
                <ellipse cx="75" cy="75" rx="10" ry="20"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # All three children should be at svg level in order
        assert len(svg) == 3
        assert get_local_tag(svg[0]) == "rect"
        assert get_local_tag(svg[1]) == "circle"
        assert get_local_tag(svg[2]) == "ellipse"

    def test_selective_unwrapping(self) -> None:
        """Test that only unwrappable groups are unwrapped."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <rect x="0" y="0" width="100" height="100"/>
            </g>
            <g opacity="0.5">
                <circle cx="50" cy="50" r="25"/>
            </g>
            <g>
                <ellipse cx="75" cy="75" rx="10" ry="20"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # First and third groups unwrapped, second preserved
        assert len(svg) == 3
        assert get_local_tag(svg[0]) == "rect"
        assert get_local_tag(svg[1]) == "g"  # Preserved (has opacity)
        assert svg[1].get("opacity") == "0.5"
        assert get_local_tag(svg[2]) == "ellipse"

    def test_no_groups_to_unwrap(self) -> None:
        """Test SVG with no groups remains unchanged."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="100" height="100"/>
            <circle cx="50" cy="50" r="25"/>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Should remain unchanged
        assert len(svg) == 2
        assert get_local_tag(svg[0]) == "rect"
        assert get_local_tag(svg[1]) == "circle"

    def test_complex_real_world_structure(self) -> None:
        """Test unwrapping in complex nested structure."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <g opacity="0.8">
                    <rect x="0" y="0" width="100" height="100"/>
                </g>
                <g>
                    <circle cx="50" cy="50" r="25"/>
                </g>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)
        svg_utils.unwrap_groups(svg)

        # Outer group unwrapped, inner group with opacity preserved
        assert len(svg) == 2
        assert get_local_tag(svg[0]) == "g"  # Preserved (has opacity)
        assert svg[0].get("opacity") == "0.8"
        assert get_local_tag(svg[1]) == "circle"  # Inner unwrappable group unwrapped

    def test_integration_with_other_optimizations(self) -> None:
        """Test full pipeline: consolidate → deduplicate → unwrap."""
        svg_str = """
        <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <linearGradient id="g1">
                    <stop offset="0%" stop-color="red"/>
                </linearGradient>
            </g>
            <defs>
                <linearGradient id="g2">
                    <stop offset="0%" stop-color="red"/>
                </linearGradient>
            </defs>
            <g>
                <rect fill="url(#g1)"/>
            </g>
            <g>
                <circle fill="url(#g2)"/>
            </g>
        </svg>
        """
        svg = ET.fromstring(svg_str)

        # Apply full optimization pipeline
        svg_utils.consolidate_defs(svg)
        svg_utils.deduplicate_definitions(svg)
        svg_utils.unwrap_groups(svg)

        # Should have consolidated defs + unwrapped groups
        assert get_local_tag(svg[0]) == "defs"
        # After deduplication, only one gradient
        assert len(svg[0]) == 1
        # After unwrapping, rect and circle at root level
        assert len(svg) == 3  # defs + rect + circle
        assert get_local_tag(svg[1]) == "rect"
        assert get_local_tag(svg[2]) == "circle"
