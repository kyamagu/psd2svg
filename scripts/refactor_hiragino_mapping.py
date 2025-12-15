#!/usr/bin/env python3
"""
Refactor _font_mapping_data.py to generate Hiragino weight variants dynamically.

This script replaces the auto-generated Hiragino entries with a generator function
that populates the missing weight variants at module import time.
"""

from pathlib import Path

# Generator function code to be inserted
GENERATOR_CODE = '''

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


def _generate_hiragino_weights() -> None:
    """
    Generate missing Hiragino font weight variants (W0-W9) for all Hiragino families.

    This function scans the FONT_MAPPING for existing Hiragino font entries with weight
    suffixes (e.g., "HiraKakuStd-W3") and automatically generates the missing W0-W9
    variants for each font family.

    This approach keeps the base mapping clean and readable while ensuring complete
    coverage of all 10 Japanese weight grades.
    """
    # Find all Hiragino fonts with weight suffixes
    hiragino_families: dict[str, dict[str, set[str]]] = {}

    for postscript_name, font_data in list(FONT_MAPPING.items()):
        # Check if it's a Hiragino font with weight suffix
        if ('Hiragino' in postscript_name or 'Hira' in postscript_name) and '-W' in postscript_name:
            base_name = postscript_name.rsplit('-W', 1)[0]
            weight_suffix = postscript_name.rsplit('-W', 1)[1]  # "0", "1", ..., "9"

            if base_name not in hiragino_families:
                hiragino_families[base_name] = {
                    "family": font_data["family"],
                    "weights": set()
                }

            hiragino_families[base_name]["weights"].add(weight_suffix)

    # Generate missing weight variants
    generated_count = 0
    for base_name in sorted(hiragino_families.keys()):
        family_name = hiragino_families[base_name]["family"]
        existing_weights = hiragino_families[base_name]["weights"]

        # Generate W0-W9 variants
        for weight_suffix, weight_value in _JAPANESE_WEIGHTS.items():
            weight_num = weight_suffix[1:]  # "W0" -> "0", etc.

            if weight_num not in existing_weights:
                postscript_name = f"{base_name}-{weight_suffix}"
                FONT_MAPPING[postscript_name] = {
                    "family": family_name,
                    "style": weight_suffix,
                    "weight": weight_value,
                }
                generated_count += 1


# Generate Hiragino weight variants at module import time
_generate_hiragino_weights()
'''


def main():
    # Read the current file
    mapping_file = Path(__file__).parent.parent / "src" / "psd2svg" / "core" / "_font_mapping_data.py"

    with open(mapping_file, 'r') as f:
        lines = f.readlines()

    # Find where auto-generated section starts
    auto_gen_line = None
    for i, line in enumerate(lines):
        if '# Additional Hiragino weight variants (auto-generated)' in line:
            auto_gen_line = i
            break

    if auto_gen_line is None:
        print("✗ Could not find auto-generated section marker")
        return

    print(f"Found auto-generated section at line {auto_gen_line + 1}")
    print(f"Removing {len(lines) - auto_gen_line} lines")

    # Keep everything before the auto-generated section
    new_lines = lines[:auto_gen_line]

    # Close the FONT_MAPPING dict
    new_lines.append("}\n")

    # Add the generator function
    new_lines.append(GENERATOR_CODE)

    # Write the refactored file
    with open(mapping_file, 'w') as f:
        f.writelines(new_lines)

    print(f"✓ Successfully refactored {mapping_file}")
    print(f"  Original lines: {len(lines)}")
    print(f"  New lines: {len(new_lines)}")
    print(f"  Reduction: {len(lines) - len(new_lines)} lines")

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
                            if ('Hiragino' in k or 'Hira' in k) and '-W' in k)
        print(f"  Hiragino entries: {hiragino_count}")

    except Exception as e:
        print(f"✗ Error loading refactored file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
