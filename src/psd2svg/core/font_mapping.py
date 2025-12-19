"""Font mapping utilities for resolving PostScript names without fontconfig.

This module provides fallback font resolution when fontconfig is unavailable
(e.g., on Windows). It uses a predefined mapping of PostScript names to font
family names, styles, and weights.

The font mappings are stored as JSON resource files in the data directory:
- default_fonts.json: ~539 core fonts (Arial, Times, Adobe fonts, etc.)
- morisawa_fonts.json: 4,042 Morisawa fonts for Japanese typography

Hiragino fonts (~370 variants) are generated dynamically using pattern-based
weight expansion (W0-W9 pattern).

Font mappings are lazy-loaded on first access for optimal performance.
"""

import functools
import json
import logging
from importlib.resources import files
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_font_json(
    filename: str, description: str, error_context: str
) -> dict[str, dict[str, Any]]:
    """Load font mapping from JSON resource file.

    Args:
        filename: Name of the JSON file in psd2svg.data package.
        description: Description for debug logging (e.g., "default fonts").
        error_context: Context message for error logging (e.g., "Using empty mapping").

    Returns:
        Dictionary mapping PostScript names to font metadata.
        Returns empty dict if loading fails (graceful degradation).
    """
    try:
        data_path = files("psd2svg.data").joinpath(filename)
        font_data_json = data_path.read_text(encoding="utf-8")
        mapping = json.loads(font_data_json)
        logger.debug(f"Loaded {len(mapping)} {description} from resource file")
        return mapping
    except Exception as e:
        logger.warning(f"Failed to load {description}: {e}. {error_context}")
        return {}


@functools.lru_cache(maxsize=1)
def _load_default_fonts() -> dict[str, dict[str, Any]]:
    """Load default font mapping on first access (lazy loading with caching).

    Returns ~539 static font entries. Does not include Hiragino variants
    (those are generated separately) or Morisawa fonts.

    Returns:
        Dictionary mapping PostScript names to font metadata.
        Returns empty dict if loading fails (graceful degradation).
    """
    return _load_font_json(
        "default_fonts.json", "default fonts", "Using empty mapping."
    )


@functools.lru_cache(maxsize=1)
def _load_morisawa_fonts() -> dict[str, dict[str, Any]]:
    """Load Morisawa font mapping on first access (lazy loading with caching).

    Returns 4,042 Morisawa font entries.

    Returns:
        Dictionary mapping PostScript names to font metadata.
        Returns empty dict if loading fails (graceful degradation).
    """
    return _load_font_json(
        "morisawa_fonts.json", "Morisawa fonts", "Continuing without Morisawa support."
    )


@functools.lru_cache(maxsize=1)
def _get_hiragino_mapping() -> dict[str, dict[str, Any]]:
    """Generate Hiragino font weight variants (W0-W9 pattern).

    This preserves the existing pattern-based generation logic.
    Generated once per process and cached.

    Returns:
        Dictionary of ~370 Hiragino font variants.
    """
    # Lazy import for performance - only load when Hiragino fonts are needed
    from psd2svg.core._font_mapping_data import (  # noqa: PLC0415
        _HIRAGINO_BASE_FONTS,
        _JAPANESE_WEIGHTS,
        _generate_weight_variants,
    )

    return _generate_weight_variants(_HIRAGINO_BASE_FONTS, _JAPANESE_WEIGHTS)


@functools.lru_cache(maxsize=1)
def get_all_font_mappings() -> dict[str, dict[str, Any]]:
    """Get combined font mapping from all sources.

    This is primarily for backward compatibility and testing.
    Most code should use find_in_mapping() directly.

    Priority order (later sources override earlier ones):
    1. Morisawa (lowest priority, added first)
    2. Hiragino generated (overrides Morisawa)
    3. Default static (highest priority, overrides all)

    Returns:
        Combined dict with all font mappings (Morisawa + Hiragino + default).
    """
    combined = {}
    # Add in reverse priority order (lowest to highest)
    combined.update(_load_morisawa_fonts())  # Lowest priority
    combined.update(_get_hiragino_mapping())  # Medium priority
    combined.update(_load_default_fonts())  # Highest priority
    logger.debug(f"Combined font mapping contains {len(combined)} fonts")
    return combined


def find_in_mapping(
    postscript_name: str, custom_mapping: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any] | None:
    """Find font information in mapping dictionaries.

    Resolution order:
    1. Custom mapping (if provided by user)
    2. Default static mapping (539 fonts, lazy loaded)
    3. Hiragino generated mapping (370 fonts, generated on first call)
    4. Morisawa mapping (4,042 fonts, lazy loaded)

    Args:
        postscript_name: PostScript name of the font (e.g., "ArialMT", "Arial-BoldMT").
        custom_mapping: Optional custom font mapping dictionary that takes priority
                       over the default mapping.

    Returns:
        Dictionary with keys: "family", "style", "weight" (float).
        Returns None if font not found in any mapping.

    Example:
        >>> mapping = {"ArialMT": {"family": "Arial", "style": "Regular",
        ...                        "weight": 80.0}}
        >>> find_in_mapping("ArialMT", mapping)
        {'family': 'Arial', 'style': 'Regular', 'weight': 80.0}
        >>> find_in_mapping("UnknownFont", mapping)
        None
    """
    # 1. Check custom mapping first (highest priority)
    if custom_mapping and postscript_name in custom_mapping:
        font_data = custom_mapping[postscript_name]
        logger.debug(f"Found '{postscript_name}' in custom font mapping")
        return _validate_font_data(font_data, postscript_name)

    # 2. Check default mapping (lazy loaded)
    default_mapping = _load_default_fonts()
    if postscript_name in default_mapping:
        font_data = default_mapping[postscript_name]
        logger.debug(f"Found '{postscript_name}' in default font mapping")
        return _validate_font_data(font_data, postscript_name)

    # 3. Check Hiragino generated mapping (generated once, cached)
    hiragino_mapping = _get_hiragino_mapping()
    if postscript_name in hiragino_mapping:
        font_data = hiragino_mapping[postscript_name]
        logger.debug(f"Found '{postscript_name}' in Hiragino font mapping")
        return _validate_font_data(font_data, postscript_name)

    # 4. Check Morisawa mapping (lazy loaded, lowest priority)
    morisawa_mapping = _load_morisawa_fonts()
    if postscript_name in morisawa_mapping:
        font_data = morisawa_mapping[postscript_name]
        logger.debug(f"Found '{postscript_name}' in Morisawa font mapping")
        return _validate_font_data(font_data, postscript_name)

    logger.debug(f"Font '{postscript_name}' not found in any mapping")
    return None


def load_font_mapping_from_json(file_path: str | Path) -> dict[str, dict[str, Any]]:
    """Load custom font mapping from a JSON file.

    Args:
        file_path: Path to JSON file containing font mappings.

    Returns:
        Dictionary mapping PostScript names to font metadata.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the JSON structure is invalid.

    Example JSON format:
        {
            "ArialMT": {
                "family": "Arial",
                "style": "Regular",
                "weight": 80.0
            },
            "Arial-BoldMT": {
                "family": "Arial",
                "style": "Bold",
                "weight": 200.0
            }
        }
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Font mapping file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in font mapping file '{file_path}': {e.msg}",
            e.doc,
            e.pos,
        ) from e

    # Validate the structure
    if not isinstance(mapping, dict):
        raise ValueError(
            f"Font mapping must be a dictionary, got {type(mapping).__name__}"
        )

    # Validate each entry
    for postscript_name, font_data in mapping.items():
        if not isinstance(postscript_name, str):
            raise ValueError(
                f"PostScript name must be a string, "
                f"got {type(postscript_name).__name__}"
            )
        _validate_font_data(font_data, postscript_name, raise_on_error=True)

    logger.info(f"Loaded {len(mapping)} font mappings from '{file_path}'")
    return mapping


def _validate_font_data(
    font_data: Any, postscript_name: str, raise_on_error: bool = False
) -> dict[str, Any] | None:
    """Validate font data structure.

    Args:
        font_data: Font data dictionary to validate.
        postscript_name: PostScript name (for error messages).
        raise_on_error: If True, raise ValueError on validation errors.
                       If False, log warning and return None.

    Returns:
        Validated font data dictionary, or None if invalid (when raise_on_error=False).

    Raises:
        ValueError: If validation fails and raise_on_error=True.
    """
    if not isinstance(font_data, dict):
        msg = (
            f"Font data for '{postscript_name}' must be a dictionary, "
            f"got {type(font_data).__name__}"
        )
        if raise_on_error:
            raise ValueError(msg)
        logger.warning(msg)
        return None

    # Check required fields
    required_fields = {"family", "style", "weight"}
    missing_fields = required_fields - set(font_data.keys())
    if missing_fields:
        msg = (
            f"Font data for '{postscript_name}' missing required fields: "
            f"{', '.join(sorted(missing_fields))}"
        )
        if raise_on_error:
            raise ValueError(msg)
        logger.warning(msg)
        return None

    # Validate field types
    if not isinstance(font_data["family"], str):
        msg = (
            f"Font family for '{postscript_name}' must be a string, "
            f"got {type(font_data['family']).__name__}"
        )
        if raise_on_error:
            raise ValueError(msg)
        logger.warning(msg)
        return None

    if not isinstance(font_data["style"], str):
        msg = (
            f"Font style for '{postscript_name}' must be a string, "
            f"got {type(font_data['style']).__name__}"
        )
        if raise_on_error:
            raise ValueError(msg)
        logger.warning(msg)
        return None

    # Weight can be int or float
    if not isinstance(font_data["weight"], (int, float)):
        msg = (
            f"Font weight for '{postscript_name}' must be a number, "
            f"got {type(font_data['weight']).__name__}"
        )
        if raise_on_error:
            raise ValueError(msg)
        logger.warning(msg)
        return None

    # Return validated data with weight as float
    return {
        "family": font_data["family"],
        "style": font_data["style"],
        "weight": float(font_data["weight"]),
    }


# For backward compatibility: expose combined mapping as DEFAULT_FONT_MAPPING
# This will trigger lazy loading on first access
DEFAULT_FONT_MAPPING = get_all_font_mappings()
