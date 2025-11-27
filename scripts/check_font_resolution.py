#!/usr/bin/env python3
"""Diagnostic script to check font resolution via fontconfig.

This helps debug issues where fonts resolve to unexpected fallbacks.
"""

import sys

try:
    import fontconfig
except ImportError:
    print("Error: fontconfig-py is not installed")
    print("Install it with: pip install fontconfig-py")
    sys.exit(1)


def check_postscript_font(postscript_name: str) -> None:
    """Check how a PostScript font name resolves."""
    print(f"\nChecking PostScript name: '{postscript_name}'")
    print("-" * 60)

    match = fontconfig.match(
        pattern=f":postscriptname={postscript_name}",
        select=("file", "family", "style", "weight", "postscriptname"),
    )

    if not match:
        print("❌ No match found")
        return

    print("✓ Match found:")
    print(f"  Family name:     {match.get('family')}")
    print(f"  PostScript name: {match.get('postscriptname')}")
    print(f"  Style:           {match.get('style')}")
    print(f"  Weight:          {match.get('weight')}")
    print(f"  File:            {match.get('file')}")


def check_family_font(family_name: str) -> None:
    """Check how a family name resolves."""
    print(f"\nChecking family name: '{family_name}'")
    print("-" * 60)

    match = fontconfig.match(
        pattern=f":family={family_name}",
        select=("file", "family", "style", "weight", "postscriptname"),
    )

    if not match:
        print("❌ No match found")
        return

    returned_family = match.get("family", "")
    if returned_family.lower() != family_name.lower():
        print(
            f"⚠️  FALLBACK: Requested '{family_name}' but got '{returned_family}'"
        )
    else:
        print("✓ Exact match found:")

    print(f"  Family name:     {match.get('family')}")
    print(f"  PostScript name: {match.get('postscriptname')}")
    print(f"  Style:           {match.get('style')}")
    print(f"  Weight:          {match.get('weight')}")
    print(f"  File:            {match.get('file')}")


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("Font Resolution Diagnostic Tool")
    print("=" * 60)

    # Check the PostScript name from the PSD file
    check_postscript_font("NotoSansJP-Regular")

    # Check common Noto font families
    for family in [
        "Noto Sans JP",
        "Noto Sans CJK JP",
        "Noto Sans",
        "Noto Sans Yi",
    ]:
        check_family_font(family)

    print("\n" + "=" * 60)
    print("\nNote: If 'Noto Sans JP' resolves to a different font like")
    print("'Noto Sans Yi', it means 'Noto Sans JP' is not installed.")
    print("\nInstall Noto Sans JP:")
    print("  Ubuntu/Debian: sudo apt-get install fonts-noto-cjk")
    print("  macOS: brew install --cask font-noto-sans-cjk-jp")


if __name__ == "__main__":
    main()
