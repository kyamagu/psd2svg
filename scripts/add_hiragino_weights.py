#!/usr/bin/env python3
"""
Script to generate and add missing Hiragino font weight variants to _font_mapping_data.py

This script analyzes existing Hiragino font entries and generates missing W0-W9 weight
variants for all Hiragino font families.
"""

from collections import defaultdict
from pathlib import Path

# Japanese weight system (W0-W9)
WEIGHTS = {
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


def extract_hiragino_families(font_mapping: dict) -> dict:
    """Extract all Hiragino font families and their existing weights."""
    families = defaultdict(lambda: {"family": None, "weights": set()})

    for postscript_name, font_data in font_mapping.items():
        # Check if it's a Hiragino font with weight suffix
        if ('Hiragino' in postscript_name or 'Hira' in postscript_name) and '-W' in postscript_name:
            base = postscript_name.rsplit('-W', 1)[0]
            weight = postscript_name.rsplit('-W', 1)[1]

            # Store the family name and existing weights
            families[base]["family"] = font_data["family"]
            families[base]["weights"].add(weight)

    return dict(families)


def generate_missing_entries(families: dict) -> list[tuple[str, dict]]:
    """Generate missing weight entries for each family."""
    new_entries = []

    for base_name in sorted(families.keys()):
        family_name = families[base_name]["family"]
        existing_weights = families[base_name]["weights"]

        # Generate missing weights (W0-W9)
        for weight_suffix, weight_value in WEIGHTS.items():
            # Extract just the number from "W0", "W1", etc.
            weight_num = weight_suffix[1:]  # "W0" -> "0", "W1" -> "1", etc.

            if weight_num not in existing_weights:
                postscript_name = f"{base_name}-{weight_suffix}"
                entry_data = {
                    "family": family_name,
                    "style": weight_suffix,
                    "weight": weight_value,
                }
                new_entries.append((postscript_name, entry_data))

    return new_entries


def format_entry(postscript_name: str, data: dict, indent: int = 4) -> str:
    """Format a single font mapping entry as Python code."""
    indent_str = " " * indent
    return f'''{indent_str}"{postscript_name}": {{
{indent_str}    "family": "{data['family']}",
{indent_str}    "style": "{data['style']}",
{indent_str}    "weight": {data['weight']},
{indent_str}}},'''


def main():
    # Import the current font mapping
    from psd2svg.core._font_mapping_data import FONT_MAPPING

    print("Analyzing current Hiragino font coverage...")
    families = extract_hiragino_families(FONT_MAPPING)

    print(f"Found {len(families)} Hiragino font families")
    print()

    # Show current coverage
    incomplete = []
    for base, info in families.items():
        existing = len(info["weights"])
        if existing < 10:
            incomplete.append((base, 10 - existing, info["family"]))

    incomplete.sort(key=lambda x: x[1], reverse=True)

    print(f"Incomplete families: {len(incomplete)}")
    print("Sample incomplete families:")
    for base, missing, family in incomplete[:5]:
        print(f"  {base}: missing {missing} weights")
    print()

    # Generate missing entries
    print("Generating missing entries...")
    new_entries = generate_missing_entries(families)
    print(f"Generated {len(new_entries)} new entries")
    print()

    # Output the generated code
    print("Generated Python code:")
    print("=" * 70)
    print()
    print("    # Additional Hiragino weight variants (auto-generated)")
    for postscript_name, data in new_entries[:10]:  # Show first 10 as sample
        print(format_entry(postscript_name, data))

    if len(new_entries) > 10:
        print(f"    # ... ({len(new_entries) - 10} more entries) ...")

    print()
    print("=" * 70)
    print()
    print(f"Total entries to add: {len(new_entries)}")
    print(f"Current total: {len(FONT_MAPPING)}")
    print(f"New total: {len(FONT_MAPPING) + len(new_entries)}")
    print()

    # Ask user if they want to append to file
    response = input("Append these entries to _font_mapping_data.py? (yes/no): ").strip().lower()

    if response == 'yes':
        # Find the _font_mapping_data.py file
        mapping_file = Path(__file__).parent.parent / "src" / "psd2svg" / "core" / "_font_mapping_data.py"

        # Read the current file
        with open(mapping_file, 'r') as f:
            content = f.read()

        # Find the last entry before the closing brace
        # We'll insert before the final "}\n" of the FONT_MAPPING dict
        if content.rstrip().endswith('}'):
            # Find the last entry
            lines = content.rstrip().split('\n')

            # Generate all entries
            new_lines = []
            new_lines.append("    # Additional Hiragino weight variants (auto-generated)")
            for postscript_name, data in new_entries:
                new_lines.append(format_entry(postscript_name, data).rstrip())

            # Insert before the closing brace
            lines.insert(-1, '\n'.join(new_lines))

            # Write back
            with open(mapping_file, 'w') as f:
                f.write('\n'.join(lines) + '\n')

            print(f"✓ Successfully added {len(new_entries)} entries to {mapping_file}")
        else:
            print("✗ Could not find proper insertion point in file")
    else:
        print("Cancelled. No changes made.")


if __name__ == "__main__":
    main()
