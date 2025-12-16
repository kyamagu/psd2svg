"""Convert Morisawa fonts from JSON Lines to JSON dict format.

This script:
1. Reads the Morisawa font file (JSON Lines format)
2. Converts to standard JSON dict format
3. Detects conflicts with default fonts
4. Saves both the converted file and a conflict report
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_morisawa_fonts(source_path: Path) -> dict[str, dict[str, Any]]:
    """Load Morisawa fonts from JSON Lines file.

    Args:
        source_path: Path to the JSON Lines file.

    Returns:
        Dictionary mapping PostScript names to font metadata.
    """
    morisawa_fonts = {}

    with open(source_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                ps_name = data["postscript_name"]

                # Convert to our format (drop postscript_name from dict)
                morisawa_fonts[ps_name] = {
                    "family": data["family"],
                    "style": data["style"],
                    "weight": float(data["weight"]),  # Ensure float
                }
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Skipping invalid line {line_num}: {e}")
                continue

    return morisawa_fonts


def load_default_fonts(default_path: Path) -> dict[str, dict[str, Any]]:
    """Load default fonts from JSON file.

    Args:
        default_path: Path to the default fonts JSON file.

    Returns:
        Dictionary mapping PostScript names to font metadata.
    """
    with open(default_path, encoding="utf-8") as f:
        return json.load(f)


def find_conflicts(
    default_fonts: dict[str, dict[str, Any]],
    morisawa_fonts: dict[str, dict[str, Any]],
) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """Find PostScript names that exist in both mappings.

    Args:
        default_fonts: Default font mapping.
        morisawa_fonts: Morisawa font mapping.

    Returns:
        List of (postscript_name, default_data, morisawa_data) tuples.
    """
    conflicts = []
    for ps_name in morisawa_fonts:
        if ps_name in default_fonts:
            conflicts.append((ps_name, default_fonts[ps_name], morisawa_fonts[ps_name]))
    return conflicts


def write_conflict_report(
    conflicts: list[tuple[str, dict[str, Any], dict[str, Any]]],
    default_count_before: int,
    default_count_after: int,
    morisawa_count: int,
    output_path: Path,
) -> None:
    """Write conflict report to file.

    Args:
        conflicts: List of conflicts found.
        default_count_before: Number of default fonts before removal.
        default_count_after: Number of default fonts after removal.
        morisawa_count: Number of Morisawa fonts.
        output_path: Path to write the report.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Morisawa Font Conflicts Report\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write(f"Total Morisawa fonts: {morisawa_count}\n")
        f.write(f"Total default fonts before: {default_count_before}\n")
        f.write(f"Conflicts found: {len(conflicts)}\n")
        f.write(f"Removed from default: {len(conflicts)}\n")
        f.write(f"Default fonts after: {default_count_after}\n\n")

        if conflicts:
            f.write("Conflicts resolved (Morisawa fonts kept, removed from default):\n")
            f.write("-" * 70 + "\n\n")

            for idx, (ps_name, default_data, morisawa_data) in enumerate(
                sorted(conflicts), start=1
            ):
                f.write(f"{idx}. {ps_name}\n")
                f.write(
                    f"   Default (REMOVED):  {default_data['family']} | "
                    f"{default_data['style']} | {default_data['weight']}\n"
                )
                f.write(
                    f"   Morisawa (KEPT):    {morisawa_data['family']} | "
                    f"{morisawa_data['style']} | {morisawa_data['weight']}\n"
                )
                f.write("   Decision: Keep Morisawa (authoritative source)\n\n")
        else:
            f.write("No conflicts found.\n")


def main() -> None:
    """Convert Morisawa fonts and resolve conflicts."""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    morisawa_source = project_root / "tmp" / "morisawa-202510.json"
    default_fonts_path = script_dir.parent / "data" / "default_fonts.json"
    morisawa_output = script_dir.parent / "data" / "morisawa_fonts.json"
    conflict_report_path = project_root / "morisawa_conflicts.txt"

    # Ensure data directory exists
    morisawa_output.parent.mkdir(parents=True, exist_ok=True)

    # Load Morisawa fonts
    print(f"Loading Morisawa fonts from {morisawa_source}...")
    morisawa_fonts = load_morisawa_fonts(morisawa_source)
    print(f"Loaded {len(morisawa_fonts)} Morisawa fonts")

    # Load default fonts
    print(f"Loading default fonts from {default_fonts_path}...")
    default_fonts = load_default_fonts(default_fonts_path)
    default_count_before = len(default_fonts)
    print(f"Loaded {default_count_before} default fonts")

    # Find conflicts
    print("Finding conflicts...")
    conflicts = find_conflicts(default_fonts, morisawa_fonts)
    print(f"Found {len(conflicts)} conflicts")

    # Remove conflicts from default fonts (Morisawa takes priority)
    if conflicts:
        print("Removing conflicts from default fonts...")
        for ps_name, _, _ in conflicts:
            del default_fonts[ps_name]

        # Save updated default fonts
        print(f"Saving updated default fonts to {default_fonts_path}...")
        with open(default_fonts_path, "w", encoding="utf-8") as f:
            json.dump(default_fonts, f, indent=2, ensure_ascii=False, sort_keys=True)

    default_count_after = len(default_fonts)

    # Save Morisawa fonts
    print(f"Saving Morisawa fonts to {morisawa_output}...")
    with open(morisawa_output, "w", encoding="utf-8") as f:
        json.dump(morisawa_fonts, f, indent=2, ensure_ascii=False, sort_keys=True)

    # Write conflict report
    print(f"Writing conflict report to {conflict_report_path}...")
    write_conflict_report(
        conflicts,
        default_count_before,
        default_count_after,
        len(morisawa_fonts),
        conflict_report_path,
    )

    # Summary
    print("\n" + "=" * 70)
    print("Conversion complete!")
    print("=" * 70)
    print(f"Morisawa fonts: {len(morisawa_fonts)}")
    print(f"Default fonts: {default_count_before} → {default_count_after}")
    print(f"Conflicts resolved: {len(conflicts)}")
    print(f"Conflict report: {conflict_report_path}")


if __name__ == "__main__":
    main()
