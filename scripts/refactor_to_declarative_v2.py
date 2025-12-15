#!/usr/bin/env python3
"""
Refactor _font_mapping_data.py to use a declarative list of base names.

This script removes all Hiragino entries from FONT_MAPPING and replaces them with
a declarative list that generates all W0-W9 variants programmatically.
"""

from pathlib import Path


# New declarative code structure to be appended
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
# All weight variants (W0-W9) will be automatically generated
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
    # Read the current file
    mapping_file = Path(__file__).parent.parent / "src" / "psd2svg" / "core" / "_font_mapping_data.py"

    with open(mapping_file, 'r') as f:
        lines = f.readlines()

    print("Analyzing current file...")
    print(f"Total lines: {len(lines)}")

    # Find and remove all Hiragino entries
    new_lines = []
    removed_count = 0
    in_hiragino_entry = False
    skip_until_next_entry = False

    for i, line in enumerate(lines):
        # Check if this is a Hiragino entry start
        if line.strip().startswith('"') and ('-W' in line):
            postscript_name = line.strip().split('"')[1]
            if 'Hiragino' in postscript_name or 'Hira' in postscript_name or 'Koburina' in postscript_name:
                in_hiragino_entry = True
                skip_until_next_entry = True
                removed_count += 1
                continue

        # Skip lines that are part of a Hiragino entry
        if skip_until_next_entry:
            # Check if we've reached the end of this entry
            if line.strip() == '},':
                skip_until_next_entry = False
                in_hiragino_entry = False
                continue
            else:
                continue

        new_lines.append(line)

    # Find the closing brace of FONT_MAPPING
    closing_brace_idx = None
    for i in range(len(new_lines) - 1, -1, -1):
        if new_lines[i].strip() == '}':
            closing_brace_idx = i
            break

    if closing_brace_idx is None:
        print("✗ Could not find closing brace of FONT_MAPPING")
        return

    # Insert declarative code before the closing brace
    final_lines = new_lines[:closing_brace_idx]
    final_lines.append(DECLARATIVE_CODE)
    final_lines.append('\n')

    # Write the refactored file
    with open(mapping_file, 'w') as f:
        f.writelines(final_lines)

    print(f"\n✓ Successfully refactored {mapping_file}")
    print(f"  Original lines: {len(lines)}")
    print(f"  New lines: {len(final_lines)}")
    print(f"  Reduction: {len(lines) - len(final_lines)} lines ({100 * (len(lines) - len(final_lines)) / len(lines):.1f}%)")
    print(f"  Removed Hiragino entries: {removed_count}")

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

        # Verify all families have W0-W9
        from collections import defaultdict
        families = defaultdict(set)
        for k in FONT_MAPPING.keys():
            if ('Hiragino' in k or 'Hira' in k or 'Koburina' in k) and '-W' in k:
                base = k.rsplit('-W', 1)[0]
                weight = k.rsplit('-W', 1)[1]
                families[base].add(weight)

        complete = sum(1 for weights in families.values() if len(weights) == 10)
        print(f"  Complete families (W0-W9): {complete}/{len(families)}")

    except Exception as e:
        print(f"✗ Error loading refactored file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
