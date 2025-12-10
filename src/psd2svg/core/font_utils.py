import base64
import dataclasses
import logging
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self

try:
    import fontconfig

    HAS_FONTCONFIG = True
except ImportError:
    HAS_FONTCONFIG = False

from psd2svg import font_subsetting
from psd2svg.core import font_mapping as _font_mapping

# Windows font resolution
if sys.platform == "win32":
    from psd2svg.core import windows_fonts as _windows_fonts  # type: ignore[import]

    HAS_WINDOWS_FONTS = True
else:
    _windows_fonts = None  # type: ignore[assignment]
    HAS_WINDOWS_FONTS = False

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class FontInfo:
    """Font information from fontconfig.

    Attributes:
        postscript_name: PostScript name of the font.
        file: Path to the font file.
        family: Family name.
        style: Style name.
        weight: Weight value. 80.0 is regular and 200.0 is bold.
        charset: Optional set of Unicode codepoints (integers) used with this font.
            This is populated during font resolution to track which characters are
            actually used with this font for subsetting purposes. The codepoints
            are converted to characters only when needed for font subsetting.
    """

    postscript_name: str
    file: str
    family: str
    style: str
    weight: float
    charset: set[int] | None = None

    @property
    def family_name(self) -> str:
        """Get the family name."""
        return self.family

    @property
    def bold(self) -> bool:
        """Whether the font is bold."""
        # TODO: Should we consider style names as well?
        return self.weight >= 200

    @property
    def italic(self) -> bool:
        """Whether the font is italic."""
        return "italic" in self.style.lower()

    def is_resolved(self) -> bool:
        """Check if font has been resolved to an actual system font file.

        A font is considered resolved if it has a valid file path pointing
        to an existing font file on the system.

        Returns:
            True if font has a valid file path, False otherwise.

        Example:
            >>> # Font from static mapping (not resolved)
            >>> font_info = FontInfo.find_static('ArialMT')
            >>> font_info.is_resolved()
            False
            >>> # Font with file path (resolved)
            >>> resolved = FontInfo.find_with_files('ArialMT')
            >>> if resolved:
            ...     resolved.is_resolved()
            True
        """
        return bool(self.file and os.path.exists(self.file))

    def get_css_weight(self, semantic: bool = False) -> int | str:
        """Get CSS font-weight value from fontconfig weight.

        Fontconfig uses numeric weights where:
        - 0 = thin (CSS 100)
        - 40 = extralight (CSS 200)
        - 50 = light (CSS 300)
        - 80 = regular/normal (CSS 400)
        - 100 = medium (CSS 500)
        - 180 = semibold (CSS 600)
        - 200 = bold (CSS 700)
        - 205 = extrabold (CSS 800)
        - 210 = black (CSS 900)

        Args:
            semantic: If True, return semantic keyword for common weights
                     ("normal", "bold") instead of numeric values.
                     Numeric values are more precise and work better with
                     variable fonts.

        Returns:
            CSS font-weight value (100-900) or semantic keyword
            ("normal" for 400, "bold" for 700).
        """
        # Map fontconfig weights to CSS weights
        # Based on fontconfig documentation and common practice
        if self.weight <= 0:
            numeric_weight = 100  # thin
        elif self.weight <= 40:
            numeric_weight = 200  # extralight
        elif self.weight <= 50:
            numeric_weight = 300  # light
        elif self.weight < 80:
            numeric_weight = 350  # semilight (CSS 3 allows non-100 multiples)
        elif self.weight <= 80:
            numeric_weight = 400  # normal/regular
        elif self.weight < 180:
            numeric_weight = 500  # medium
        elif self.weight < 200:
            numeric_weight = 600  # semibold
        elif self.weight <= 200:
            numeric_weight = 700  # bold
        elif self.weight <= 205:
            numeric_weight = 800  # extrabold
        else:
            numeric_weight = 900  # black/heavy

        # Return semantic keyword if requested and applicable
        if semantic:
            if numeric_weight == 400:
                return "normal"
            elif numeric_weight == 700:
                return "bold"

        return numeric_weight

    @property
    def css_weight(self) -> int:
        """Get numeric CSS font-weight value (100-900).

        This is a convenience property that calls get_css_weight(semantic=False).
        For more control, use get_css_weight() directly.

        Returns:
            CSS font-weight value (100-900).
        """
        result = self.get_css_weight(semantic=False)
        assert isinstance(result, int)
        return result

    def to_dict(self) -> dict[str, str | float]:
        """Convert FontInfo to a serializable dictionary.

        Returns:
            Dictionary representation of the font information.
        """
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str | float]) -> Self:
        """Create FontInfo from a dictionary.

        Args:
            data: Dictionary containing font information.

        Returns:
            FontInfo instance.
        """
        return cls(
            postscript_name=str(data["postscript_name"]),
            file=str(data["file"]),
            family=str(data["family"]),
            style=str(data["style"]),
            weight=float(data["weight"]),
        )

    def to_font_face_css(self, data_uri: str) -> str:
        """Generate @font-face CSS rule for this font.

        Args:
            data_uri: Base64 data URI for the font file (e.g., 'data:font/ttf;base64,...').

        Returns:
            CSS @font-face rule string.

        Example:
            >>> font_info = FontInfo.find('Arial-Regular')
            >>> data_uri = encode_font_data_uri(font_info.file)
            >>> css = font_info.to_font_face_css(data_uri)
            >>> print(css)
            @font-face {
              font-family: 'Arial';
              src: url(data:font/ttf;base64,...);
              font-weight: 400;
              font-style: normal;
            }
        """
        font_style = "italic" if self.italic else "normal"
        css_weight = self.css_weight

        return f"""@font-face {{
  font-family: '{self.family}';
  src: url({data_uri});
  font-weight: {css_weight};
  font-style: {font_style};
}}"""

    @staticmethod
    def _match_fontconfig(
        postscriptname: str, charset_codepoints: set[int] | None
    ) -> dict[str, Any] | None:
        """Match font via fontconfig with optional charset support.

        This is a low-level helper that performs the actual fontconfig matching
        with optional charset-based filtering. Used by both find() and resolve().

        Args:
            postscriptname: PostScript name of the font.
            charset_codepoints: Optional set of Unicode codepoints for charset matching.
                               Empty sets are treated as None (no charset matching).

        Returns:
            fontconfig match result dict with keys: file, family, style, weight.
            None if no match found.

        Raises:
            Exception: If fontconfig matching fails and charset_codepoints is None or empty.
        """
        try:
            if charset_codepoints:
                # Use charset-based matching
                logger.debug(
                    f"Using charset with {len(charset_codepoints)} codepoints "
                    f"for '{postscriptname}'"
                )
                charset = fontconfig.CharSet.from_codepoints(sorted(charset_codepoints))
                match = fontconfig.match(
                    properties={
                        "postscriptname": postscriptname,
                        "charset": charset,
                    },
                    select=("file", "family", "style", "weight"),
                )
            else:
                # Standard PostScript name matching
                match = fontconfig.match(
                    pattern=f":postscriptname={postscriptname}",
                    select=("file", "family", "style", "weight"),
                )
            return match  # type: ignore
        except Exception as e:
            # Graceful degradation: fall back to name-only matching
            if charset_codepoints:
                logger.warning(
                    f"Charset-based matching failed for '{postscriptname}': {e}. "
                    "Falling back to name-only matching"
                )
                match = fontconfig.match(
                    pattern=f":postscriptname={postscriptname}",
                    select=("file", "family", "style", "weight"),
                )
                return match  # type: ignore
            else:
                # If name-only matching also failed, re-raise
                raise

    @staticmethod
    def _match_windows(
        postscriptname: str, charset_codepoints: set[int] | None
    ) -> dict[str, Any] | None:
        """Match font via Windows registry with optional charset support.

        This is a low-level helper that performs the actual Windows registry matching
        with optional charset-based filtering. Used by both find() and resolve().

        Args:
            postscriptname: PostScript name of the font.
            charset_codepoints: Optional set of Unicode codepoints for charset matching.
                               Empty sets are treated as None (no charset matching).

        Returns:
            Windows font resolver match result dict with keys: file, family, style, weight.
            None if no match found.

        Raises:
            Exception: If Windows matching fails and charset_codepoints is None or empty.
        """
        resolver = _windows_fonts.get_windows_font_resolver()  # type: ignore[attr-defined]

        try:
            if charset_codepoints:
                # Use charset-based matching
                logger.debug(
                    f"Using charset with {len(charset_codepoints)} codepoints "
                    f"for '{postscriptname}'"
                )
                match = resolver.find_with_charset(postscriptname, charset_codepoints)
            else:
                # Standard PostScript name matching
                match = resolver.find(postscriptname)
            return match  # type: ignore
        except Exception as e:
            # Graceful degradation: fall back to name-only matching
            if charset_codepoints:
                logger.warning(
                    f"Charset-based matching failed for '{postscriptname}': {e}. "
                    "Falling back to name-only matching"
                )
                match = resolver.find(postscriptname)
                return match  # type: ignore
            else:
                # If name-only matching also failed, re-raise
                raise

    @staticmethod
    def _find_via_fontconfig(
        postscriptname: str, charset_codepoints: set[int] | None
    ) -> Self | None:
        """Find font via fontconfig with optional charset matching.

        Args:
            postscriptname: PostScript name of the font.
            charset_codepoints: Optional set of Unicode codepoints for charset matching.
                               Empty sets are treated as None (no charset matching).

        Returns:
            FontInfo object if found, None otherwise. If charset_codepoints is provided
            and non-empty, the returned FontInfo will have charset populated for later resolution.
        """
        logger.debug(
            f"Font '{postscriptname}' not in static mapping, trying fontconfig..."
        )

        match = FontInfo._match_fontconfig(postscriptname, charset_codepoints)

        if match:
            logger.info(
                f"Resolved '{postscriptname}' via fontconfig fallback: "
                f"{match['family']}"
            )
            # Store codepoints directly
            charset: set[int] | None = charset_codepoints

            return FontInfo(
                postscript_name=postscriptname,
                file=match["file"],  # type: ignore
                family=match["family"],  # type: ignore
                style=match["style"],  # type: ignore
                weight=match["weight"],  # type: ignore
                charset=charset,
            )

        return None

    @staticmethod
    def _find_via_windows(
        postscriptname: str, charset_codepoints: set[int] | None
    ) -> Self | None:
        """Find font via Windows registry with optional charset matching.

        Args:
            postscriptname: PostScript name of the font.
            charset_codepoints: Optional set of Unicode codepoints for charset matching.
                               Empty sets are treated as None (no charset matching).

        Returns:
            FontInfo object if found, None otherwise. If charset_codepoints is provided
            and non-empty, the returned FontInfo will have charset populated for later resolution.
        """
        logger.debug(
            f"Font '{postscriptname}' not in static mapping, trying Windows registry..."
        )

        match = FontInfo._match_windows(postscriptname, charset_codepoints)

        if match:
            logger.info(
                f"Resolved '{postscriptname}' via Windows registry fallback: "
                f"{match['family']}"
            )
            # Store codepoints directly
            charset: set[int] | None = charset_codepoints

            return FontInfo(
                postscript_name=postscriptname,
                file=str(match["file"]),
                family=str(match["family"]),
                style=str(match["style"]),
                weight=float(match["weight"]),
                charset=charset,
            )

        return None

    @staticmethod
    def find(
        postscriptname: str,
        font_mapping: dict[str, dict[str, float | str]] | None = None,
        charset_codepoints: set[int] | None = None,
        disable_static_mapping: bool = False,
    ) -> Self | None:
        """Find font information by PostScript name (backward-compatible wrapper).

        This method is kept for backward compatibility. New code should use the more
        explicit methods:
        - find_static() for CSS family names (embed_fonts=False scenarios)
        - find_with_files() for font embedding (embed_fonts=True scenarios)

        This wrapper delegates to the appropriate method based on disable_static_mapping:
        - If disable_static_mapping=False: Uses find_static() (name resolution only)
        - If disable_static_mapping=True: Uses find_with_files() (with file paths)

        Args:
            postscriptname: PostScript name of the font (e.g., "ArialMT").
            font_mapping: Optional custom font mapping dictionary. Format:
                         {"PostScriptName": {"family": str, "style": str, "weight": float}}
            charset_codepoints: Optional set of Unicode codepoints for charset-based
                               font matching. Only used when disable_static_mapping=True
                               (platform resolution). Empty sets are treated as None
                               (no charset matching). Default: None.
            disable_static_mapping: If True, use find_with_files(); if False, use find_static().
                                   Default: False.

        Returns:
            FontInfo object with font metadata, or None if font not found.

        Example:
            >>> # Standard resolution (static mapping)
            >>> font = FontInfo.find('ArialMT')
            >>> # Is equivalent to:
            >>> font = FontInfo.find_static('ArialMT')
            >>>
            >>> # Font embedding resolution (platform-specific)
            >>> font = FontInfo.find('ArialMT', disable_static_mapping=True)
            >>> # Is equivalent to:
            >>> font = FontInfo.resolve('ArialMT')
        """
        if disable_static_mapping:
            return FontInfo.resolve(postscriptname, font_mapping, charset_codepoints)
        else:
            return FontInfo.find_static(postscriptname, font_mapping)

    @staticmethod
    def find_static(
        postscriptname: str,
        font_mapping: dict[str, dict[str, float | str]] | None = None,
    ) -> Self | None:
        """Find font using custom and static mappings only (no platform resolution).

        This method resolves PostScript names to CSS font families without accessing
        system fonts. It is suitable for SVG generation when embed_fonts=False, where
        only CSS font family names are needed and platform-specific font substitution
        would cause visual artifacts.

        Resolution order:
        1. Custom font mapping (if provided)
        2. Static font mapping (572 common fonts)
        3. Return None if not found (preserves PostScript name in SVG)

        Args:
            postscriptname: PostScript name of the font (e.g., "ArialMT").
            font_mapping: Optional custom font mapping dictionary. Takes priority
                         over static mapping. Format:
                         {"PostScriptName": {"family": str, "style": str, "weight": float}}

        Returns:
            FontInfo object with family/style/weight (no file path), or None if not found.
            When None is returned, the PostScript name will be preserved in the SVG output.

        Example:
            >>> # Resolve common font (found in static mapping)
            >>> font = FontInfo.find_static('ArialMT')
            >>> assert font.family == 'Arial'
            >>> assert font.file == ''  # No file path
            >>>
            >>> # Resolve uncommon font (not in static mapping)
            >>> font = FontInfo.find_static('UnknownFont')
            >>> assert font is None  # Preserves PostScript name in SVG
        """
        # 1. Check custom mapping first
        if font_mapping:
            custom_data = _font_mapping.find_in_mapping(postscriptname, font_mapping)
            if custom_data:
                logger.debug(
                    f"Resolved '{postscriptname}' via custom font mapping: "
                    f"{custom_data['family']}"
                )
                return FontInfo(
                    postscript_name=postscriptname,
                    file="",
                    family=str(custom_data["family"]),
                    style=str(custom_data["style"]),
                    weight=float(custom_data["weight"]),
                )

        # 2. Check static mapping
        static_data = _font_mapping.find_in_mapping(postscriptname, None)
        if static_data:
            logger.debug(
                f"Resolved '{postscriptname}' via static font mapping: "
                f"{static_data['family']}"
            )
            return FontInfo(
                postscript_name=postscriptname,
                file="",
                family=str(static_data["family"]),
                style=str(static_data["style"]),
                weight=float(static_data["weight"]),
            )

        # 3. Not found - return None (no platform fallback)
        logger.debug(
            f"Font '{postscriptname}' not found in static mapping. "
            "Keeping PostScript name in SVG."
        )
        return None

    @staticmethod
    def _resolve_from_custom_mapping_with_file(
        postscriptname: str,
        font_mapping: dict[str, dict[str, float | str]],
        charset_codepoints: set[int] | None = None,
    ) -> Self | None:
        """Resolve font from custom mapping with file validation.

        This helper method handles custom font mapping resolution when file paths
        are required (e.g., for font embedding). It validates that the mapping
        contains all required fields and that the font file exists.

        Args:
            postscriptname: PostScript name of the font (e.g., "ArialMT").
            font_mapping: Custom font mapping dictionary.
            charset_codepoints: Optional Unicode codepoints (unused but kept for
                               consistency with resolve() signature).

        Returns:
            FontInfo with file path if found and valid, None otherwise.
            Falls back to None if file missing or doesn't exist.
        """
        _ = charset_codepoints  # Unused but kept for signature consistency

        # Check if font exists in custom mapping (access raw data directly)
        if postscriptname not in font_mapping:
            return None

        custom_data = font_mapping[postscriptname]

        # Validate custom mapping has required fields including file path
        if not (
            "family" in custom_data
            and "style" in custom_data
            and "weight" in custom_data
            and "file" in custom_data
            and custom_data["file"]  # Must be non-empty
        ):
            # Custom mapping found but missing file path - fall back to platform resolution
            logger.debug(
                f"Custom mapping for '{postscriptname}' found but missing 'file' field. "
                "Falling back to platform resolution."
            )
            return None

        file_path = str(custom_data["file"])
        # Validate file exists
        if not os.path.exists(file_path):
            logger.warning(
                f"Custom mapping for '{postscriptname}' specifies file '{file_path}' "
                "but file does not exist. Falling back to platform resolution."
            )
            return None

        logger.debug(
            f"Resolved '{postscriptname}' via custom font mapping with file path: "
            f"{file_path}"
        )
        return FontInfo(
            postscript_name=postscriptname,
            file=file_path,
            family=str(custom_data["family"]),
            style=str(custom_data["style"]),
            weight=float(custom_data["weight"]),
        )

    @staticmethod
    def resolve(
        postscriptname: str,
        font_mapping: dict[str, dict[str, float | str]] | None = None,
        charset_codepoints: set[int] | None = None,
    ) -> Self | None:
        """Resolve font with file path using platform-specific resolution.

        Uses fontconfig (Linux/macOS) or Windows registry to locate font files.
        Suitable for font embedding where actual font files are needed.

        Args:
            postscriptname: PostScript name of the font (e.g., "ArialMT").
            font_mapping: Optional custom mapping with file paths. Must include "file"
                         field with existing font file path. Format:
                         {"PostScriptName": {"family": str, "style": str,
                                            "weight": float, "file": str}}
                         If mapping lacks "file" field or file doesn't exist, falls back
                         to platform resolution.
            charset_codepoints: Optional Unicode codepoints for charset-based matching.
                               Prioritizes fonts with better glyph coverage.
                               Empty sets are treated as None (no charset matching).

        Returns:
            FontInfo with non-empty file path, or None if not found. File path is
            guaranteed to be non-empty when FontInfo is returned.

        Example:
            >>> font = FontInfo.resolve('ArialMT')
            >>> if font:
            ...     print(f"Font file: {font.file}")  # Always has file path
        """
        # 1. Check custom mapping first (must have file path for embedding)
        if font_mapping:
            resolved = FontInfo._resolve_from_custom_mapping_with_file(
                postscriptname, font_mapping, charset_codepoints
            )
            if resolved:
                return resolved

        # 2. Platform-specific resolution (skip static mapping - optimization)
        # Try fontconfig (Linux/macOS)
        if HAS_FONTCONFIG:
            result = FontInfo._find_via_fontconfig(postscriptname, charset_codepoints)
            if result:
                return result

        # Try Windows registry (Windows)
        elif HAS_WINDOWS_FONTS:
            result = FontInfo._find_via_windows(postscriptname, charset_codepoints)
            if result:
                return result

        # 3. Not found
        if not HAS_FONTCONFIG and not HAS_WINDOWS_FONTS:
            logger.warning(
                f"Font '{postscriptname}' not found: "
                "platform-specific font resolution not available. "
                "Consider providing a custom font mapping via the font_mapping parameter."
            )
        else:
            platform_name = "fontconfig" if HAS_FONTCONFIG else "Windows registry"
            logger.warning(
                f"Font '{postscriptname}' not found via {platform_name}. "
                "Make sure the font is installed on your system, or provide a custom "
                "font mapping via the font_mapping parameter."
            )
        return None


def encode_font_data_uri(font_path: str) -> str:
    """Encode a font file as a base64 data URI.

    Args:
        font_path: Absolute path to the font file.

    Returns:
        Data URI string (e.g., 'data:font/ttf;base64,...').

    Raises:
        FileNotFoundError: If font file doesn't exist.
        IOError: If font file can't be read.

    Example:
        >>> data_uri = encode_font_data_uri('/usr/share/fonts/arial.ttf')
        >>> print(data_uri[:50])
        data:font/ttf;base64,AAEAAAATAQAABAAwR1BPUw...
    """
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")

    # Determine MIME type from file extension
    ext = os.path.splitext(font_path)[1].lower()
    mime_types = {
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }
    mime_type = mime_types.get(ext, "font/ttf")  # Default to ttf

    # Read and encode font file
    try:
        with open(font_path, "rb") as f:
            font_data = f.read()
    except IOError as e:
        raise IOError(f"Failed to read font file '{font_path}': {e}") from e

    base64_data = base64.b64encode(font_data).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"


def encode_font_bytes_to_data_uri(font_bytes: bytes, font_format: str) -> str:
    """Encode font bytes as a base64 data URI.

    This function is used for embedding subset or converted fonts that
    are already in memory as bytes (e.g., from fontTools subsetting).

    Args:
        font_bytes: Font file data as bytes.
        font_format: Font format - "ttf", "otf", or "woff2".

    Returns:
        Data URI string (e.g., 'data:font/woff2;base64,...').

    Raises:
        ValueError: If font_format is unsupported.

    Example:
        >>> font_bytes = b'...'  # Subset font data
        >>> data_uri = encode_font_bytes_to_data_uri(font_bytes, "woff2")
        >>> print(data_uri[:30])
        data:font/woff2;base64,d09GMg...
    """
    mime_types = {
        "ttf": "font/ttf",
        "otf": "font/otf",
        "woff2": "font/woff2",
    }

    if font_format not in mime_types:
        raise ValueError(
            f"Unsupported font format: {font_format}. "
            f"Supported formats: {', '.join(mime_types.keys())}"
        )

    mime_type = mime_types[font_format]
    base64_data = base64.b64encode(font_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"


def encode_font_with_options(
    font_path: str,
    cache: dict[str, str],
    subset_codepoints: set[int] | None = None,
    font_format: str = "ttf",
) -> str:
    """Encode a font file as a data URI with optional subsetting and caching.

    This helper consolidates the logic for encoding fonts with subsetting
    support and cache management.

    Args:
        font_path: Path to the font file.
        cache: Dictionary to use for caching encoded data URIs.
        subset_codepoints: Optional set of Unicode codepoints (integers) to subset the font to.
            If None, the full font is encoded.
        font_format: Font format for output: "ttf", "otf", or "woff2".

    Returns:
        Data URI string for the encoded font.

    Raises:
        ImportError: If subsetting is requested but fonttools is not available.
        FileNotFoundError: If font file doesn't exist.
        IOError: If font file can't be read.

    Note:
        - Cache keys include format and codepoint count for subset fonts
        - Full fonts use just the file path as cache key
        - Missing codepoints trigger fallback to full font with warning
    """
    # Subsetting path
    if subset_codepoints:
        # Create cache key for subset fonts (include format and codepoint count)
        cache_key = f"{font_path}:{font_format}:{len(subset_codepoints)}"

        if cache_key not in cache:
            logger.debug(
                f"Subsetting font: {font_path} -> {font_format} "
                f"({len(subset_codepoints)} codepoints)"
            )
            try:
                font_bytes = font_subsetting.subset_font(  # type: ignore
                    input_path=font_path,
                    output_format=font_format,
                    unicode_codepoints=subset_codepoints,
                )
                data_uri = encode_font_bytes_to_data_uri(font_bytes, font_format)
                cache[cache_key] = data_uri
            except Exception as e:
                logger.warning(
                    f"Failed to subset font '{font_path}': {e}. "
                    "Falling back to full font"
                )
                # Fall back to full font
                if font_path not in cache:
                    logger.debug(f"Encoding full font: {font_path}")
                    cache[font_path] = encode_font_data_uri(font_path)
                return cache[font_path]
        return cache[cache_key]

    # Full font encoding path
    if font_path not in cache:
        logger.debug(f"Encoding font: {font_path}")
        cache[font_path] = encode_font_data_uri(font_path)
    return cache[font_path]


def create_charset_codepoints(chars: set[str]) -> set[int]:
    """Create set of Unicode codepoints from characters.

    This function converts a set of Unicode characters to a set of
    integer codepoints suitable for charset-based font matching.

    Args:
        chars: Set of Unicode characters (e.g., {"A", "あ", "中"}).

    Returns:
        Set of Unicode codepoints (integers). Returns empty set if chars is empty.
        Multi-codepoint characters (emoji with modifiers) are split into
        individual codepoints.

    Example:
        >>> chars = {"H", "e", "l", "o"}
        >>> codepoints = create_charset_codepoints(chars)
        >>> codepoints
        {72, 101, 108, 111}
        >>> create_charset_codepoints(set())
        set()
    """
    # Convert characters to codepoints (handles multi-codepoint characters like emoji)
    codepoint_set = set()
    for char in chars:
        for code_point in char:
            codepoint_set.add(ord(code_point))

    if codepoint_set:
        logger.debug(
            f"Created {len(codepoint_set)} codepoints from {len(chars)} characters"
        )

    return codepoint_set


def create_file_url(font_path: str) -> str:
    """Create a file:// URL from an absolute font file path.

    This function converts an absolute file path to a properly formatted file:// URL
    suitable for use in CSS @font-face rules with browser-based rasterizers like
    PlaywrightRasterizer.

    Args:
        font_path: Absolute path to the font file.

    Returns:
        File URL string (e.g., 'file:///usr/share/fonts/arial.ttf').

    Raises:
        ValueError: If font_path is not absolute.
        FileNotFoundError: If font file doesn't exist.

    Note:
        - Handles cross-platform paths (Windows, Linux, macOS)
        - Properly escapes special characters (spaces, non-ASCII)
        - Requires absolute paths (relative paths are rejected)
        - URL format: file:// + absolute_path (with proper encoding)

    Example:
        >>> # Linux/macOS
        >>> create_file_url('/usr/share/fonts/arial.ttf')
        'file:///usr/share/fonts/arial.ttf'

        >>> # Windows
        >>> create_file_url('C:\\\\Windows\\\\Fonts\\\\arial.ttf')
        'file:///C:/Windows/Fonts/arial.ttf'

        >>> # Path with spaces
        >>> create_file_url('/usr/share/fonts/My Font.ttf')
        'file:///usr/share/fonts/My%20Font.ttf'

        >>> # Non-ASCII characters
        >>> create_file_url('/fonts/日本語/font.ttf')
        'file:///fonts/%E6%97%A5%E6%9C%AC%E8%AA%9E/font.ttf'
    """
    # Validate file existence
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")

    # Ensure absolute path (required for file:// URLs)
    abs_path = os.path.abspath(font_path)

    # Convert to Path object for cross-platform handling
    path_obj = Path(abs_path)

    # Convert to POSIX path (forward slashes) for URL
    # Windows: C:\Fonts\arial.ttf -> C:/Fonts/arial.ttf -> /C:/Fonts/arial.ttf
    # Unix: /usr/share/fonts/arial.ttf -> /usr/share/fonts/arial.ttf
    if sys.platform == "win32":
        # Windows: Convert backslashes to forward slashes
        posix_path = path_obj.as_posix()
        # Ensure leading slash for Windows drive letters: C:/... -> /C:/...
        if not posix_path.startswith("/"):
            posix_path = "/" + posix_path
    else:
        # Unix: Already has leading slash
        posix_path = str(path_obj)

    # URL-encode the path to handle spaces and special characters
    # Use quote() with safe="/:@" to preserve path structure
    # - "/" must be safe (path separator)
    # - ":" must be safe (Windows drive letters)
    # - "@" is safe for potential UNC paths (though not fully supported)
    encoded_path = urllib.parse.quote(posix_path, safe="/:@")

    # Construct file:// URL
    # Format: file:// + encoded_path (already has leading /)
    # Result: file:///absolute/path or file:///C:/Windows/path
    return f"file://{encoded_path}"
