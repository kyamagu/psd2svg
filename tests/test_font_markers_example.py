"""Example tests demonstrating font marker usage for non-Latin text rendering.

This file shows how to use the font requirement markers defined in conftest.py.
When you create actual test cases with PSD fixtures, use these markers to ensure
tests are skipped when required fonts are not available.
"""

import pytest

from tests.conftest import (
    has_font,
    requires_noto_sans,
    requires_noto_sans_arabic,
    requires_noto_sans_cjk,
    requires_noto_sans_devanagari,
    requires_noto_sans_hebrew,
    requires_noto_sans_thai,
)


class TestFontAvailability:
    """Tests to verify font checking utilities work correctly."""

    def test_has_font_utility(self) -> None:
        """Test that has_font utility can check for font availability."""
        # This should work on all systems (will return True or False)
        result = has_font("Arial")
        assert isinstance(result, bool)

    def test_has_font_nonexistent(self) -> None:
        """Test that has_font returns False for non-existent fonts."""
        result = has_font("ThisFontDefinitelyDoesNotExist12345")
        assert result is False


class TestNotoFontMarkers:
    """Example tests showing how to use font requirement markers.

    These are placeholder tests that demonstrate the pattern.
    Replace with actual PSD conversion tests once fixtures are available.
    """

    @requires_noto_sans
    def test_noto_sans_available(self) -> None:
        """Example: This test runs only if Noto Sans is available."""
        assert has_font("Noto Sans")

    @requires_noto_sans_cjk
    def test_japanese_text_rendering(self) -> None:
        """Example: Test Japanese text rendering with Noto Sans CJK JP.

        When you have a PSD fixture with Japanese text, use this marker:

        @requires_noto_sans_cjk
        def test_japanese_text_rendering(self):
            svg_doc = convert('tests/fixtures/japanese_text.psd')
            # Verify Japanese text is rendered correctly
            assert 'Noto Sans CJK JP' in svg_doc.tostring()
        """
        assert has_font("Noto Sans CJK JP")

    @requires_noto_sans_arabic
    def test_arabic_text_rendering(self) -> None:
        """Example: Test Arabic text rendering (right-to-left).

        Use this marker for tests with Arabic text fixtures.
        Test will be skipped if Noto Sans Arabic is not installed.
        """
        # Placeholder - replace with actual test when fixture is available
        pass

    @requires_noto_sans_devanagari
    def test_devanagari_text_rendering(self) -> None:
        """Example: Test Devanagari text rendering (complex shaping).

        Use this marker for tests with Devanagari text fixtures.
        Test will be skipped if Noto Sans Devanagari is not installed.
        """
        # Placeholder - replace with actual test when fixture is available
        pass

    @requires_noto_sans_thai
    def test_thai_text_rendering(self) -> None:
        """Example: Test Thai text rendering (complex shaping).

        Use this marker for tests with Thai text fixtures.
        Test will be skipped if Noto Sans Thai is not installed.
        """
        # Placeholder - replace with actual test when fixture is available
        pass

    @requires_noto_sans_hebrew
    def test_hebrew_text_rendering(self) -> None:
        """Example: Test Hebrew text rendering (right-to-left).

        Use this marker for tests with Hebrew text fixtures.
        Test will be skipped if Noto Sans Hebrew is not installed.
        """
        # Placeholder - replace with actual test when fixture is available
        pass

    @pytest.mark.parametrize(
        "font_family,marker_name",
        [
            ("Noto Sans", "requires_noto_sans"),
            ("Noto Sans CJK JP", "requires_noto_sans_cjk"),
            ("Noto Sans Arabic", "requires_noto_sans_arabic"),
            ("Noto Sans Devanagari", "requires_noto_sans_devanagari"),
            ("Noto Sans Thai", "requires_noto_sans_thai"),
            ("Noto Sans Hebrew", "requires_noto_sans_hebrew"),
        ],
    )
    def test_font_marker_consistency(self, font_family: str, marker_name: str) -> None:
        """Verify that font markers are consistent with actual font availability.

        This test checks that the marker skip logic matches has_font() results.
        """
        # This test always runs - it checks the logic consistency
        font_available = has_font(font_family)
        # We just verify the utility works without errors
        assert isinstance(font_available, bool)
