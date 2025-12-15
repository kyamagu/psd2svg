#!/usr/bin/env python3
"""
Refactor _font_mapping_data.py to use a declarative list of base names.

This script replaces all Hiragino entries with a simple list of (base_name, family_name)
tuples and generates all W0-W9 variants programmatically.
"""

from pathlib import Path
from collections import defaultdict


def extract_hiragino_base_names():
    """Extract unique Hiragino base names and their families from current mapping."""
    from psd2svg.core._font_mapping_data import FONT_MAPPING

    families = {}
    for postscript_name, font_data in FONT_MAPPING.items():
        if ('Hiragino' in postscript_name or 'Hira' in postscript_name) and '-W' in postscript_name:
            base = postscript_name.rsplit('-W', 1)[0]
            families[base] = font_data["family"]

    return families


# New declarative code structure
DECLARATIVE_CODE = '''
# Japanese weight system (W0-W9) used by Hiragino fonts
_JAPANESE_WEIGHTS = {
    "W0": 0.0,
    "W1": 40.0,
    "W2": 45.0,
    "W3": 50.0,
    "W4": 80.0,
    "W5": 100.0,
    "W6": 180.0,
    "W7": 200.0,
    "W8": 205.0,
    "W9": 210.0,
}

# Hiragino font base names with their family names
# All variants (W0-W9) will be automatically generated
_HIRAGINO_BASE_FONTS = [
    # Modern Hiragino Sans/Serif (macOS 10.11+)
    ("HiraginoSans", "Hiragino Sans"),
    ("HiraginoSerif", "Hiragino Serif"),
    ("HiraginoSansGB", "Hiragino Sans GB"),
    # Hiragino Kaku Gothic Std/Pro/ProN (角ゴ - Square Gothic)
    ("HiraKakuStd", "Hiragino Kaku Gothic Std"),
    ("HiraKakuPro", "Hiragino Kaku Gothic Pro"),
    ("HiraKakuProN", "Hiragino Kaku Gothic ProN"),
    ("HiraKakuStdN", "Hiragino Kaku Gothic StdN"),
    # Hiragino Sans Pr6N/Upr variants (newer naming)
    ("HiraginoSansPr6N", "Hiragino Sans"),
    ("HiraginoSansUpr", "Hiragino Sans"),
    # Hiragino Maru Gothic (丸ゴ - Rounded Gothic)
    ("HiraMaruStd", "Hiragino Maru Gothic Std"),
    ("HiraMaruPro", "Hiragino Maru Gothic Pro"),
    ("HiraMaruProN", "Hiragino Maru Gothic ProN"),
    ("HiraMaruStdN", "Hiragino Maru Gothic StdN"),
    # Hiragino Sans R (Rounded) Pr6N/Upr variants
    ("HiraginoSansRPr6N", "Hiragino Maru Gothic"),
    ("HiraginoSansRUpr", "Hiragino Maru Gothic"),
    # Hiragino Mincho (明朝 - Serif/Ming)
    ("HiraMinStd", "Hiragino Mincho Std"),
    ("HiraMinPro", "Hiragino Mincho Pro"),
    ("HiraMinProN", "Hiragino Mincho ProN"),
    ("HiraMinStdN", "Hiragino Mincho StdN"),
    # Hiragino Serif Pr6N/Upr variants
    ("HiraginoSerifPr6N", "Hiragino Serif"),
    ("HiraginoSerifUpr", "Hiragino Serif"),
    # Hiragino Gyosho (行書 - Semi-cursive/Running script)
    ("HiraGyoStd", "Hiragino Gyosho Std"),
    ("HiraGyoStdN", "Hiragino Gyosho StdN"),
    # Hiragino UD (Universal Design) series
    ("HiraginoUDSansStd", "Hiragino UD Sans Std"),
    ("HiraginoUDSansStdN", "Hiragino UD Sans StdN"),
    ("HiraginoUDSansFStd", "Hiragino UD Sans F Std"),
    ("HiraginoUDSansFStdN", "Hiragino UD Sans F StdN"),
    ("HiraginoUDSansRStd", "Hiragino UD Maru Gothic Std"),
    ("HiraginoUDSansRStdN", "Hiragino UD Maru Gothic StdN"),
    ("HiraginoUDSerifStd", "Hiragino UD Serif Std"),
    ("HiraginoUDSerifStdN", "Hiragino UD Serif StdN"),
    # Hiragino Sans Old variants
    ("HiraSansOldStd", "Hiragino Sans Old Std"),
    ("HiraSansOldStdN", "Hiragino Sans Old StdN"),
    ("HiraginoSansROldStd", "Hiragino Maru Gothic Old Std"),
    ("HiraginoSansROldStdN", "Hiragino Maru Gothic Old StdN"),
    # Other Hiragino variants
    ("KoburinaGoStd", "Koburina Gothic Std"),
    ("KoburinaGoStdN", "Koburina Gothic StdN"),
]


def _generate_weight_variants(
    base_fonts: list[tuple[str, str]],
    weights: dict[str, float],
    suffix_pattern: str = "-W{weight}",
) -> dict[str, dict[str, Any]]:
    """
    Generate font entries with weight variants.

    Args:
        base_fonts: List of (base_name, family_name) tuples
        weights: Dict mapping weight suffix (e.g., "W0") to weight value
        suffix_pattern: Pattern for generating PostScript names (default: "-W{weight}")

    Returns:
        Dictionary of generated font entries
    """
    entries = {}
    for base_name, family_name in base_fonts:
        for weight_suffix, weight_value in weights.items():
            postscript_name = base_name + suffix_pattern.format(weight=weight_suffix)
            entries[postscript_name] = {
                "family": family_name,
                "style": weight_suffix,
                "weight": weight_value,
            }
    return entries


# Generate and add Hiragino weight variants to FONT_MAPPING at module import time
FONT_MAPPING.update(_generate_weight_variants(_HIRAGINO_BASE_FONTS, _JAPANESE_WEIGHTS))
'''


def main():
    # Extract current Hiragino families to verify we have all of them
    print("Extracting current Hiragino font families...")
    families = extract_hiragino_base_names()

    print(f"Found {len(families)} unique Hiragino base fonts:")
    for base in sorted(families.keys()):
        print(f"  {base}: {families[base]}")
    print()

    # Read the current file
    mapping_file = Path(__file__).parent.parent / "src" / "psd2svg" / "core" / "_font_mapping_data.py"

    with open(mapping_file, 'r') as f:
        content = f.read()

    # Find the Hiragino section start
    hiragino_start = content.find("    # Hiragino family (macOS Japanese)")
    if hiragino_start == -1:
        print("✗ Could not find Hiragino section")
        return

    # Find where the closing brace and generator function start
    closing_brace = content.find("\n}\n\n\n# Japanese weight system")
    if closing_brace == -1:
        print("✗ Could not find closing brace")
        return

    print(f"Hiragino section: lines ~{content[:hiragino_start].count(chr(10)) + 1}")
    print(f"Closing brace: line ~{content[:closing_brace].count(chr(10)) + 1}")

    # Keep everything before Hiragino section
    new_content = content[:hiragino_start]

    # Close the FONT_MAPPING dict
    new_content += "}\n"

    # Add the declarative code
    new_content += DECLARATIVE_CODE

    # Write the refactored file
    with open(mapping_file, 'w') as f:
        f.write(new_content)

    old_lines = content.count('\n')
    new_lines = new_content.count('\n')

    print(f"\n✓ Successfully refactored {mapping_file}")
    print(f"  Original lines: {old_lines}")
    print(f"  New lines: {new_lines}")
    print(f"  Reduction: {old_lines - new_lines} lines ({100 * (old_lines - new_lines) / old_lines:.1f}%)")

    # Verify the new file loads correctly
    print("\nVerifying the refactored file...")
    try:
        # Force reload the module
        import sys
        if 'psd2svg.core._font_mapping_data' in sys.modules:
            del sys.modules['psd2svg.core._font_mapping_data']

        from psd2svg.core._font_mapping_data import FONT_MAPPING

        print(f"✓ File loads successfully")
        print(f"  Total font entries: {len(FONT_MAPPING)}")

        # Check Hiragino coverage
        hiragino_count = sum(1 for k in FONT_MAPPING.keys()
                            if ('Hiragino' in k or 'Hira' in k or 'Koburina' in k) and '-W' in k)
        print(f"  Hiragino entries: {hiragino_count}")

    except Exception as e:
        print(f"✗ Error loading refactored file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
