"""Tests for paint functionality."""

from unittest.mock import Mock
from xml.etree import ElementTree as ET

import pytest
from psd_tools.api.layers import Layer
from psd_tools.constants import Tag
from psd_tools.psd import descriptor
from psd_tools.psd.tagged_blocks import ListElement, TaggedBlocks
from psd_tools.terminology import Key, Unit

from psd2svg.core.paint import PaintConverter


class TestPatternTransform:
    """Test pattern transform handling."""

    @pytest.fixture
    def converter(self):
        """Create a minimal PaintConverter instance for testing."""
        converter = Mock(spec=PaintConverter)
        converter.set_pattern_transform = PaintConverter.set_pattern_transform.__get__(
            converter, PaintConverter
        )
        return converter

    @pytest.fixture
    def layer(self):
        """Create a mock layer."""
        layer = Mock(spec=Layer)
        layer.tagged_blocks = TaggedBlocks()
        layer.tagged_blocks.set_data(Tag.REFERENCE_POINT, ListElement([0, 0]))  # type: ignore[list-item]
        return layer

    @pytest.fixture
    def offset_layer(self):
        """Create a mock layer."""
        layer = Mock(spec=Layer)
        layer.tagged_blocks = TaggedBlocks()
        layer.tagged_blocks.set_data(Tag.REFERENCE_POINT, ListElement([0, 12]))  # type: ignore[list-item]
        return layer

    @pytest.fixture
    def node(self):
        """Create a test XML element."""
        return ET.Element("pattern")

    @pytest.fixture
    def empty_setting(self):
        """Create a mock empty descriptor setting."""
        desc = descriptor.Descriptor()
        return desc

    @pytest.fixture
    def angle_scale_setting(self):
        """Create a mock empty descriptor setting."""
        desc = descriptor.Descriptor()
        desc[Key.Angle] = descriptor.UnitFloat(unit=Unit.Angle, value=45.0)
        desc[Key.Scale] = descriptor.UnitFloat(unit=Unit.Percent, value=50.0)
        return desc

    def test_pattern_transform_empty(self, converter, layer, node, empty_setting):
        """Test that setting an empty descriptor does not have pattern transform."""
        converter.set_pattern_transform(layer, empty_setting, node)
        assert "patternTransform" not in node.attrib

    def test_pattern_transform_angle_scale(
        self, converter, layer, node, angle_scale_setting
    ):
        """Test that setting angle and scale updates pattern transform."""
        converter.set_pattern_transform(layer, angle_scale_setting, node)
        assert "patternTransform" in node.attrib
        assert node.attrib["patternTransform"] == "scale(0.5) rotate(-45)"

    def test_pattern_transform_with_offset(
        self, converter, offset_layer, node, angle_scale_setting
    ):
        """Test that setting angle and scale with offset updates pattern transform."""
        converter.set_pattern_transform(offset_layer, angle_scale_setting, node)
        assert "patternTransform" in node.attrib
        assert (
            node.attrib["patternTransform"] == "translate(0,12) scale(0.5) rotate(-45)"
        )
