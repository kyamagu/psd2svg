"""Tests for blend mode warning functionality."""

import logging
from unittest.mock import Mock
from xml.etree import ElementTree as ET

import pytest
from psd_tools.constants import BlendMode
from psd_tools.terminology import Enum

from psd2svg.core.layer import LayerConverter


class TestBlendModeWarnings:
    """Test that warnings are emitted for inaccurate blend modes."""

    @pytest.fixture
    def converter(self):
        """Create a minimal LayerConverter instance for testing."""
        converter = Mock(spec=LayerConverter)
        converter.set_blend_mode = LayerConverter.set_blend_mode.__get__(
            converter, LayerConverter
        )
        return converter

    @pytest.fixture
    def node(self):
        """Create a test XML element."""
        return ET.Element("g")

    def test_dissolve_blend_mode_warning(self, converter, node, caplog):
        """Test that dissolve blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.DISSOLVE, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "DISSOLVE" in caplog.text or "Dissolve" in caplog.text
        assert "normal" in caplog.text

    def test_linear_burn_blend_mode_warning(self, converter, node, caplog):
        """Test that linear burn blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.LINEAR_BURN, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "LINEAR_BURN" in caplog.text or "Linear" in caplog.text
        assert "plus-darker" in caplog.text

    def test_linear_dodge_blend_mode_warning(self, converter, node, caplog):
        """Test that linear dodge blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.LINEAR_DODGE, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "LINEAR_DODGE" in caplog.text or "Linear" in caplog.text
        assert "plus-lighter" in caplog.text

    def test_bytes_linear_burn_blend_mode_warning(self, converter, node, caplog):
        """Test that bytes linearBurn also triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(b"linearBurn", node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "plus-darker" in caplog.text

    def test_bytes_linear_dodge_blend_mode_warning(self, converter, node, caplog):
        """Test that bytes linearDodge also triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(b"linearDodge", node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "plus-lighter" in caplog.text

    def test_pin_light_blend_mode_warning(self, converter, node, caplog):
        """Test that pin light blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.PIN_LIGHT, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "normal" in caplog.text

    def test_hard_mix_blend_mode_warning(self, converter, node, caplog):
        """Test that hard mix blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.HARD_MIX, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "normal" in caplog.text

    def test_darker_color_blend_mode_warning(self, converter, node, caplog):
        """Test that darker color blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.DARKER_COLOR, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "darken" in caplog.text

    def test_lighter_color_blend_mode_warning(self, converter, node, caplog):
        """Test that lighter color blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.LIGHTER_COLOR, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "lighten" in caplog.text

    def test_vivid_light_blend_mode_warning(self, converter, node, caplog):
        """Test that vivid light blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.VIVID_LIGHT, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "lighten" in caplog.text

    def test_linear_light_blend_mode_warning(self, converter, node, caplog):
        """Test that linear light blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.LINEAR_LIGHT, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "darken" in caplog.text

    def test_subtract_blend_mode_warning(self, converter, node, caplog):
        """Test that subtract blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.SUBTRACT, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "difference" in caplog.text

    def test_divide_blend_mode_warning(self, converter, node, caplog):
        """Test that divide blend mode triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.DIVIDE, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "difference" in caplog.text

    def test_enum_dissolve_blend_mode_warning(self, converter, node, caplog):
        """Test that Enum.Dissolve also triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(Enum.Dissolve, node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "normal" in caplog.text

    def test_bytes_vivid_light_blend_mode_warning(self, converter, node, caplog):
        """Test that bytes blend mode also triggers a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(b'vividLight', node)

        assert len(caplog.records) == 1
        assert "not accurately supported" in caplog.text
        assert "lighten" in caplog.text

    def test_accurate_blend_mode_no_warning(self, converter, node, caplog):
        """Test that accurate blend modes don't trigger warnings."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.MULTIPLY, node)

        # Should have no warnings
        assert len(caplog.records) == 0

    def test_normal_blend_mode_no_warning(self, converter, node, caplog):
        """Test that normal blend mode doesn't trigger a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.NORMAL, node)

        assert len(caplog.records) == 0

    def test_screen_blend_mode_no_warning(self, converter, node, caplog):
        """Test that screen blend mode doesn't trigger a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.SCREEN, node)

        assert len(caplog.records) == 0

    def test_overlay_blend_mode_no_warning(self, converter, node, caplog):
        """Test that overlay blend mode doesn't trigger a warning."""
        with caplog.at_level(logging.WARNING):
            converter.set_blend_mode(BlendMode.OVERLAY, node)

        assert len(caplog.records) == 0

    def test_unsupported_blend_mode_raises_error(self, converter, node):
        """Test that completely unsupported blend modes raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported blend mode"):
            converter.set_blend_mode(b"unsupported_mode", node)
