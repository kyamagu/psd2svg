"""Font mapping utilities for resolving PostScript names without fontconfig.

This module provides fallback font resolution when fontconfig is unavailable
(e.g., on Windows). It uses a predefined mapping of PostScript names to font
family names, styles, and weights.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# This will be populated by importing from _font_mapping_data.py
# For now, start with a minimal mapping that will be expanded
DEFAULT_FONT_MAPPING: dict[str, dict[str, Any]] = {}


def find_in_mapping(
    postscript_name: str, custom_mapping: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any] | None:
    """Find font information in mapping dictionaries.

    Args:
        postscript_name: PostScript name of the font (e.g., "ArialMT", "Arial-BoldMT").
        custom_mapping: Optional custom font mapping dictionary that takes priority
                       over the default mapping.

    Returns:
        Dictionary with keys: "family", "style", "weight" (float).
        Returns None if font not found in any mapping.

    Example:
        >>> mapping = {"ArialMT": {"family": "Arial", "style": "Regular", "weight": 80.0}}
        >>> find_in_mapping("ArialMT", mapping)
        {'family': 'Arial', 'style': 'Regular', 'weight': 80.0}
        >>> find_in_mapping("UnknownFont", mapping)
        None
    """
    # Check custom mapping first (if provided)
    if custom_mapping and postscript_name in custom_mapping:
        font_data = custom_mapping[postscript_name]
        logger.debug(f"Found '{postscript_name}' in custom font mapping")
        return _validate_font_data(font_data, postscript_name)

    # Fall back to default mapping
    if postscript_name in DEFAULT_FONT_MAPPING:
        font_data = DEFAULT_FONT_MAPPING[postscript_name]
        logger.debug(f"Found '{postscript_name}' in default font mapping")
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
                f"PostScript name must be a string, got {type(postscript_name).__name__}"
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


# Try to load default mapping from _font_mapping_data.py
try:
    from psd2svg.core._font_mapping_data import FONT_MAPPING

    DEFAULT_FONT_MAPPING = FONT_MAPPING
    logger.debug(f"Loaded {len(DEFAULT_FONT_MAPPING)} default font mappings")
except ImportError:
    logger.debug(
        "Default font mapping data not found. "
        "Run scripts/generate_font_mapping.py to generate it."
    )
    DEFAULT_FONT_MAPPING = {}
