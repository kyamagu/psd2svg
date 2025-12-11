"""CLI tool for generating custom font mappings from PSD files.

This tool extracts font information from PSD files and generates JSON mapping files
that can be used with the psd2svg font_mapping parameter.

Usage:
    python -m psd2svg.tools.generate_font_mapping input.psd
    python -m psd2svg.tools.generate_font_mapping *.psd -o fonts.json
    python -m psd2svg.tools.generate_font_mapping input.psd --only-missing
    python -m psd2svg.tools.generate_font_mapping input.psd --query-fontconfig
"""

import argparse
import json
import logging
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

from psd_tools import PSDImage
from psd_tools.api.layers import TypeLayer

from psd2svg.core import font_mapping as fm
from psd2svg.core.typesetting import TypeSetting

# Check if fontconfig is available
try:
    import fontconfig

    HAS_FONTCONFIG = True
except ImportError:
    HAS_FONTCONFIG = False

logger = logging.getLogger(__name__)


def extract_fonts_from_psd(psd_path: Path) -> set[str]:
    """Extract unique PostScript font names from a PSD file.

    Args:
        psd_path: Path to the PSD file.

    Returns:
        Set of PostScript font names used in the PSD file.

    Raises:
        Exception: If PSD file cannot be opened.
    """
    try:
        psd: PSDImage = PSDImage.open(psd_path)
    except Exception as e:
        raise Exception(f"Failed to open PSD file '{psd_path}': {e}") from e

    fonts = set()
    for layer in psd.descendants():
        if isinstance(layer, TypeLayer) and layer.is_visible():
            # Do whatever you want to do here
            text_setting = TypeSetting(layer._data)
            for paragraph in text_setting:
                for style in paragraph:
                    font_info = text_setting.get_font_info(style.style.font)
                    if font_info and font_info.postscript_name:
                        fonts.add(font_info.postscript_name)
    return fonts


def generate_mapping(
    psd_files: list[Path],
    only_missing: bool = False,
    query_fontconfig: bool = False,
    verbose: bool = False,
) -> dict[str, dict[str, Any]]:
    """Generate font mapping from PSD files.

    Args:
        psd_files: List of PSD file paths.
        only_missing: If True, only include fonts not in default mapping.
        query_fontconfig: If True, query fontconfig for font details.
        verbose: If True, print verbose progress messages.

    Returns:
        Dictionary mapping PostScript names to font metadata.
    """
    # Collect all fonts from all PSD files
    all_fonts = set()
    for psd_file in psd_files:
        if verbose:
            print(f"Scanning {psd_file}...")
        try:
            fonts = extract_fonts_from_psd(psd_file)
            all_fonts.update(fonts)
            if verbose:
                print(f"  Found {len(fonts)} font(s)")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            continue

    if not all_fonts:
        if verbose:
            print("No fonts found in PSD files.")
        return {}

    if verbose:
        print(f"\nTotal unique fonts: {len(all_fonts)}")

    # Generate mapping
    mapping = OrderedDict()

    fonts_in_default = 0
    fonts_missing = 0
    fonts_queried = 0

    for font in sorted(all_fonts):
        # Check if font is in default mapping
        in_default = font in fm.DEFAULT_FONT_MAPPING

        if only_missing and in_default:
            continue

        if query_fontconfig and HAS_FONTCONFIG:
            # Query fontconfig
            try:
                match = fontconfig.match(
                    pattern=f":postscriptname={font}",
                    select=("family", "style", "weight"),
                )
                if match:
                    mapping[font] = {
                        "family": match["family"],
                        "style": match["style"],
                        "weight": float(match["weight"]),
                        "_comment": "Queried from fontconfig",
                    }
                    fonts_queried += 1
                    if verbose:
                        print(f"  ✓ {font} (queried from fontconfig)")
                    continue
            except Exception:
                pass

        # Use default mapping or create empty template
        if in_default:
            default_data = fm.DEFAULT_FONT_MAPPING[font]
            mapping[font] = {
                "family": default_data["family"],
                "style": default_data["style"],
                "weight": default_data["weight"],
                "_comment": "Found in default mapping",
            }
            fonts_in_default += 1
            if verbose:
                print(f"  ✓ {font} (in default mapping)")
        else:
            mapping[font] = {
                "family": "",
                "style": "",
                "weight": 0.0,
                "_comment": "Not in default mapping - please fill in values",
            }
            fonts_missing += 1
            if verbose:
                print(f"  ✗ {font} (NOT in default mapping)")

    if verbose:
        print("\nSummary:")
        print(f"  Total fonts: {len(all_fonts)}")
        print(f"  In default mapping: {fonts_in_default}")
        print(f"  Missing from default: {fonts_missing}")
        if query_fontconfig:
            print(f"  Queried from fontconfig: {fonts_queried}")
        print(f"  Output fonts: {len(mapping)}")

    return mapping


def main() -> int:
    """Main entry point for the CLI tool.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Generate custom font mappings from PSD files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate mapping from a single PSD file
  python -m psd2svg.tools.generate_font_mapping input.psd

  # Generate mapping from multiple PSD files
  python -m psd2svg.tools.generate_font_mapping file1.psd file2.psd

  # Output to file
  python -m psd2svg.tools.generate_font_mapping input.psd -o fonts.json

  # Only show fonts NOT in default mapping
  python -m psd2svg.tools.generate_font_mapping input.psd --only-missing

  # Query fontconfig for font details (requires fontconfig)
  python -m psd2svg.tools.generate_font_mapping input.psd --query-fontconfig
        """,
    )

    parser.add_argument(
        "psd_files",
        nargs="+",
        type=Path,
        help="One or more PSD file paths",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )

    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Only output fonts NOT in default mapping",
    )

    parser.add_argument(
        "--query-fontconfig",
        action="store_true",
        help="Query fontconfig to fill in font details (requires fontconfig)",
    )

    parser.add_argument(
        "--format",
        choices=["json", "python"],
        default="json",
        help="Output format (default: json)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show progress and font details",
    )

    args = parser.parse_args()

    # Check fontconfig availability
    if args.query_fontconfig and not HAS_FONTCONFIG:
        print(
            "Error: --query-fontconfig requires fontconfig, but it's not available.",
            file=sys.stderr,
        )
        print(
            "Install fontconfig-py with: uv sync (on Linux/macOS)",
            file=sys.stderr,
        )
        return 1

    # Verify PSD files exist
    for psd_file in args.psd_files:
        if not psd_file.exists():
            print(f"Error: PSD file not found: {psd_file}", file=sys.stderr)
            return 1

    # Generate mapping
    try:
        mapping = generate_mapping(
            psd_files=args.psd_files,
            only_missing=args.only_missing,
            query_fontconfig=args.query_fontconfig,
            verbose=args.verbose,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not mapping:
        if args.verbose:
            print("\nNo fonts to output.")
        return 0

    # Format output
    if args.format == "json":
        output = json.dumps(mapping, indent=2, ensure_ascii=False)
    else:  # python
        output = "FONT_MAPPING = {\n"
        for postscript_name, font_data in mapping.items():
            output += f'    "{postscript_name}": {{\n'
            output += f'        "family": "{font_data["family"]}",\n'
            output += f'        "style": "{font_data["style"]}",\n'
            output += f'        "weight": {font_data["weight"]},\n'
            if "_comment" in font_data:
                output += f'        "_comment": "{font_data["_comment"]}",\n'
            output += "    },\n"
        output += "}\n"

    # Write output
    if args.output:
        try:
            args.output.write_text(output, encoding="utf-8")
            if args.verbose:
                print(f"\nWrote mapping to {args.output}")
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
