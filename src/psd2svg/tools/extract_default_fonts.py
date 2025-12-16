"""Extract default fonts from _font_mapping_data.py to JSON.

This script was used to initially extract the static font entries from FONT_MAPPING
(excluding generated Hiragino variants) and save them to JSON files for lazy loading.

Note: This script is kept for reference. The extraction has already been completed.
The resulting files are:
- src/psd2svg/data/default_fonts.json (539 fonts)
- src/psd2svg/data/morisawa_fonts.json (4,042 fonts)
"""

import json
from pathlib import Path
from typing import Any


def extract_static_fonts() -> dict[str, dict[str, Any]]:
    """Extract static font entries (exclude generated Hiragino variants).

    Note: This function is obsolete. The font mapping has been migrated to JSON.
    This is kept for reference only.

    Returns:
        Dictionary of static font entries only.
    """
    raise RuntimeError(
        "This extraction script is obsolete. Font mappings have been migrated to JSON.\n"
        "The resulting files are already in src/psd2svg/data/:\n"
        "  - default_fonts.json (539 fonts)\n"
        "  - morisawa_fonts.json (4,042 fonts)"
    )


def main() -> None:
    """Extract static fonts and save to JSON file.

    Note: This function is obsolete. See extract_static_fonts() for details.
    """
    extract_static_fonts()


if __name__ == "__main__":
    main()
