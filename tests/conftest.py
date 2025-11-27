import logging
import os

import pytest

from psd2svg.core.font_utils import FontInfo

logger = logging.getLogger(__name__)


def get_fixture(name: str) -> str:
    """Get a fixture by name."""
    return os.path.join(os.path.dirname(__file__), "fixtures", name)


def has_font(family: str) -> bool:
    """Check if a font family is available on the system.

    Args:
        family: Font family name to check.

    Returns:
        True if the font is available, False otherwise.
    """
    try:
        # Try to find the font using fontconfig
        import fontconfig

        match = fontconfig.match(
            pattern=f":family={family}",
            select=("family",),
        )
        # Fontconfig returns a fallback font if the requested one isn't found
        # We need to check if the returned family matches what we requested
        if not match or not match.get("family"):
            return False
        # Check if the returned family name matches (case-insensitive)
        returned_family = match.get("family", "").lower()
        requested_family = family.lower()
        return returned_family == requested_family
    except Exception as e:
        logger.debug(f"Error checking font availability: {e}")
        return False


def has_postscript_font(postscript_name: str) -> bool:
    """Check if a font with the given PostScript name is available.

    Args:
        postscript_name: PostScript name of the font.

    Returns:
        True if the font is available, False otherwise.
    """
    try:
        font_info = FontInfo.find(postscript_name)
        return font_info is not None
    except Exception as e:
        logger.debug(f"Error checking font availability: {e}")
        return False


# Pytest markers for font-dependent tests
requires_noto_sans = pytest.mark.skipif(
    not has_font("Noto Sans"),
    reason="Noto Sans font not installed",
)

requires_noto_sans_jp = pytest.mark.skipif(
    not has_font("Noto Sans JP"),
    reason="Noto Sans JP font not installed",
)

requires_noto_sans_cjk = pytest.mark.skipif(
    not has_font("Noto Sans CJK JP"),
    reason="Noto Sans CJK JP font not installed",
)

requires_noto_sans_arabic = pytest.mark.skipif(
    not has_font("Noto Sans Arabic"),
    reason="Noto Sans Arabic font not installed",
)

requires_noto_sans_devanagari = pytest.mark.skipif(
    not has_font("Noto Sans Devanagari"),
    reason="Noto Sans Devanagari font not installed",
)

requires_noto_sans_thai = pytest.mark.skipif(
    not has_font("Noto Sans Thai"),
    reason="Noto Sans Thai font not installed",
)

requires_noto_sans_hebrew = pytest.mark.skipif(
    not has_font("Noto Sans Hebrew"),
    reason="Noto Sans Hebrew font not installed",
)
