"""Windows font resolution using registry and fontTools.

This module provides font resolution on Windows by querying the Windows registry
for installed fonts and extracting PostScript names using fontTools.

Architecture:
    - Query HKLM and HKCU registry keys for font file paths
    - Parse TTF/OTF files to extract PostScript names and metadata
    - Build in-memory cache for fast lookups during session
    - Integrate with FontInfo.find() as fallback when fontconfig unavailable

Usage:
    >>> resolver = WindowsFontResolver()
    >>> font_info = resolver.find("ArialMT")
    >>> if font_info:
    ...     print(f"Found: {font_info.family} at {font_info.file}")
"""

import logging
import os
import sys
from typing import Any

from fontTools.ttLib import TTFont

logger = logging.getLogger(__name__)

# Platform-specific imports
HAS_WINREG = sys.platform == "win32"
if HAS_WINREG:
    import winreg  # type: ignore[import-not-found]


class WindowsFontResolver:
    """Windows font resolver using registry and fontTools.

    This class provides font resolution on Windows by:
    1. Querying the Windows registry for installed fonts
    2. Extracting PostScript names and metadata from font files
    3. Caching results for fast repeated lookups

    Attributes:
        _cache: In-memory cache mapping PostScript names to FontInfo dictionaries.
        _initialized: Whether the cache has been built.

    Example:
        >>> resolver = WindowsFontResolver()
        >>> font_info = resolver.find("ArialMT")
        >>> if font_info:
        ...     print(f"{font_info['family']} - {font_info['weight']}")
        Arial - 80.0
    """

    def __init__(self) -> None:
        """Initialize the Windows font resolver.

        Note:
            Cache is built lazily on first find() call to avoid startup overhead.
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._initialized = False

    def find(self, postscript_name: str) -> dict[str, Any] | None:
        """Find font information by PostScript name.

        Args:
            postscript_name: PostScript name of the font (e.g., "ArialMT").

        Returns:
            Dictionary with keys: "postscript_name", "file", "family", "style", "weight".
            Returns None if font not found.

        Example:
            >>> resolver = WindowsFontResolver()
            >>> info = resolver.find("Arial-BoldMT")
            >>> if info:
            ...     print(f"Family: {info['family']}, Weight: {info['weight']}")
            Family: Arial, Weight: 200.0
        """
        # Build cache on first use (lazy initialization)
        if not self._initialized:
            self._build_cache()

        return self._cache.get(postscript_name)

    def _build_cache(self) -> None:
        """Build font cache by scanning Windows registry and parsing font files.

        This method:
        1. Queries HKLM and HKCU registry for installed fonts
        2. Parses each font file to extract PostScript name and metadata
        3. Stores results in _cache for fast lookups

        Note:
            - Silently skips fonts that can't be parsed
            - Logs summary statistics at DEBUG level
            - Sets _initialized flag to prevent rebuilding
        """
        if not HAS_WINREG:
            logger.warning(
                "Windows registry (winreg) not available. "
                "Windows font resolution disabled."
            )
            self._initialized = True
            return

        logger.debug("Building Windows font cache...")

        # Collect font file paths from registry
        font_files = []
        font_files.extend(self._get_system_fonts())
        font_files.extend(self._get_user_fonts())

        # Remove duplicates (preserve order)
        seen = set()
        unique_files = []
        for path in font_files:
            if path not in seen:
                seen.add(path)
                unique_files.append(path)

        logger.debug(f"Found {len(unique_files)} unique font files in registry")

        # Parse font files and build cache
        parsed = 0
        skipped = 0

        for font_path in unique_files:
            try:
                font_info = self._parse_font_file(font_path)
                if font_info and font_info.get("postscript_name"):
                    ps_name = font_info["postscript_name"]
                    self._cache[ps_name] = font_info
                    parsed += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.debug(f"Failed to parse font '{font_path}': {e}")
                skipped += 1

        logger.debug(
            f"Windows font cache built: {parsed} fonts parsed, {skipped} skipped"
        )
        self._initialized = True

    def _get_system_fonts(self) -> list[str]:
        """Get system-wide font file paths from HKLM registry.

        Returns:
            List of absolute font file paths.

        Note:
            - Queries HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts
            - Converts relative paths to absolute (C:\\Windows\\Fonts)
            - Silently skips fonts that can't be accessed
        """
        fonts = []
        try:
            key = winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
            )
            try:
                # QueryInfoKey returns (num_keys, num_values, last_modified)
                num_values = winreg.QueryInfoKey(key)[1]  # type: ignore[attr-defined]
                for i in range(num_values):
                    try:
                        name, file_path, _ = winreg.EnumValue(key, i)  # type: ignore[attr-defined]
                        # Convert relative paths to absolute
                        if not os.path.isabs(file_path):
                            file_path = os.path.join(
                                os.environ.get("WINDIR", "C:\\Windows"),
                                "Fonts",
                                file_path,
                            )
                        if os.path.exists(file_path):
                            fonts.append(file_path)
                    except OSError:
                        continue
            finally:
                winreg.CloseKey(key)  # type: ignore[attr-defined]
        except OSError as e:
            logger.debug(f"Could not access system fonts registry: {e}")

        return fonts

    def _get_user_fonts(self) -> list[str]:
        """Get user-specific font file paths from HKCU registry.

        Returns:
            List of absolute font file paths.

        Note:
            - Queries HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts
            - Converts relative paths to absolute (AppData\\Local\\Microsoft\\Windows\\Fonts)
            - Silently skips fonts that can't be accessed
        """
        fonts = []
        try:
            key = winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_CURRENT_USER,  # type: ignore[attr-defined]
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
            )
            try:
                num_values = winreg.QueryInfoKey(key)[1]  # type: ignore[attr-defined]
                for i in range(num_values):
                    try:
                        name, file_path, _ = winreg.EnumValue(key, i)  # type: ignore[attr-defined]
                        # Convert relative paths to absolute
                        if not os.path.isabs(file_path):
                            user_fonts_dir = os.path.join(
                                os.environ.get("LOCALAPPDATA", ""),
                                "Microsoft",
                                "Windows",
                                "Fonts",
                            )
                            file_path = os.path.join(user_fonts_dir, file_path)
                        if os.path.exists(file_path):
                            fonts.append(file_path)
                    except OSError:
                        continue
            finally:
                winreg.CloseKey(key)  # type: ignore[attr-defined]
        except OSError as e:
            logger.debug(f"Could not access user fonts registry: {e}")

        return fonts

    def _parse_font_file(self, font_path: str) -> dict[str, Any] | None:
        """Parse font file to extract PostScript name and metadata.

        Args:
            font_path: Absolute path to font file (TTF/OTF).

        Returns:
            Dictionary with keys: "postscript_name", "file", "family", "style", "weight".
            Returns None if parsing fails or file is not a valid font.

        Note:
            - Extracts PostScript name (name ID 6)
            - Extracts family name (name ID 1 or 16)
            - Extracts style name (name ID 2 or 17)
            - Extracts weight from OS/2 table (usWeightClass)
            - Prefers Windows platform names (platform ID 3)
        """
        try:
            font = TTFont(font_path)

            # Extract PostScript name (name ID 6)
            postscript_name = self._get_name_table_entry(font, 6)
            if not postscript_name:
                return None

            # Extract family name (prefer ID 16 "Typographic Family", fallback to ID 1)
            family = self._get_name_table_entry(font, 16) or self._get_name_table_entry(
                font, 1
            )
            if not family:
                family = "Unknown"

            # Extract style name (prefer ID 17 "Typographic Subfamily", fallback to ID 2)
            style = self._get_name_table_entry(font, 17) or self._get_name_table_entry(
                font, 2
            )
            if not style:
                style = "Regular"

            # Extract weight from OS/2 table
            weight = self._get_weight_from_os2(font)

            return {
                "postscript_name": postscript_name,
                "file": font_path,
                "family": family,
                "style": style,
                "weight": float(weight),
            }

        except Exception as e:
            logger.debug(f"Failed to parse font file '{font_path}': {e}")
            return None

    def _get_name_table_entry(self, font: TTFont, name_id: int) -> str | None:
        """Extract name table entry from font.

        Args:
            font: Loaded TTFont instance.
            name_id: Name table entry ID (1=family, 2=style, 6=PostScript, etc.).

        Returns:
            Name string, or None if not found.

        Note:
            - Prefers Windows platform (3, 1, 0x409) - Windows, Unicode, US English
            - Falls back to Mac platform (1, 0, 0) - Mac, Roman, English
            - Returns first available if platform-specific lookups fail
        """
        if "name" not in font:
            return None

        name_table = font["name"]

        # Try Windows platform first (3, 1, 0x409)
        entry = name_table.getName(name_id, 3, 1, 0x409)
        if entry:
            return entry.toUnicode()

        # Try Mac platform (1, 0, 0)
        entry = name_table.getName(name_id, 1, 0, 0)
        if entry:
            return entry.toUnicode()

        # Fallback: find any entry with this name_id
        for record in name_table.names:
            if record.nameID == name_id:
                try:
                    return record.toUnicode()
                except Exception:
                    continue

        return None

    def _get_weight_from_os2(self, font: TTFont) -> float:
        """Extract font weight from OS/2 table.

        Args:
            font: Loaded TTFont instance.

        Returns:
            Weight value in fontconfig scale (0-210).
            Default: 80.0 (regular) if OS/2 table missing or invalid.

        Note:
            Converts CSS weight (100-900) to fontconfig scale:
            - 100 (thin) -> 0
            - 200 (extralight) -> 40
            - 300 (light) -> 50
            - 400 (regular) -> 80
            - 500 (medium) -> 100
            - 600 (semibold) -> 180
            - 700 (bold) -> 200
            - 800 (extrabold) -> 205
            - 900 (black) -> 210
        """
        if "OS/2" not in font:
            return 80.0  # Default: regular

        try:
            os2_table = font["OS/2"]
            css_weight = os2_table.usWeightClass

            # Convert CSS weight (100-900) to fontconfig scale
            weight_mapping = {
                100: 0.0,  # thin
                200: 40.0,  # extralight
                300: 50.0,  # light
                400: 80.0,  # regular
                500: 100.0,  # medium
                600: 180.0,  # semibold
                700: 200.0,  # bold
                800: 205.0,  # extrabold
                900: 210.0,  # black
            }

            # Find closest weight
            if css_weight in weight_mapping:
                return weight_mapping[css_weight]

            # Interpolate for non-standard weights
            if css_weight < 100:
                return 0.0
            elif css_weight > 900:
                return 210.0
            else:
                # Linear interpolation between nearest values
                lower = (css_weight // 100) * 100
                upper = lower + 100
                if lower in weight_mapping and upper in weight_mapping:
                    ratio = (css_weight - lower) / 100.0
                    return weight_mapping[lower] + ratio * (
                        weight_mapping[upper] - weight_mapping[lower]
                    )

            return 80.0  # Fallback

        except Exception:
            return 80.0  # Default on error


# Global singleton instance (lazy initialization)
_resolver: WindowsFontResolver | None = None


def get_windows_font_resolver() -> WindowsFontResolver:
    """Get or create the global Windows font resolver instance.

    Returns:
        WindowsFontResolver singleton instance.

    Note:
        Uses lazy initialization - cache is built on first find() call.

    Example:
        >>> resolver = get_windows_font_resolver()
        >>> font_info = resolver.find("ArialMT")
    """
    global _resolver
    if _resolver is None:
        _resolver = WindowsFontResolver()
    return _resolver
