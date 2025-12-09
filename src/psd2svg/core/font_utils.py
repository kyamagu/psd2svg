import base64
import dataclasses
import logging
import os
import sys
import urllib.parse
from pathlib import Path

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
    """

    postscript_name: str
    file: str
    family: str
    style: str
    weight: float

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
            >>> font_info = FontInfo.find('ArialMT')
            >>> font_info.is_resolved()
            False
            >>> # After resolution
            >>> resolved = font_info.resolve()
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

    def resolve(self, charset_codepoints: set[int] | None = None) -> Self | None:
        """Resolve font to actual available system font via fontconfig.

        This method queries fontconfig to find the actual font file and complete
        metadata for the font. When charset_codepoints is provided, resolution
        prioritizes fonts with better glyph coverage for those characters.

        Args:
            charset_codepoints: Optional set of Unicode codepoints (integers)
                to filter fonts by glyph coverage. When provided:
                - Linux/macOS: Passed to fontconfig via CharSet
                - Windows: Used to check cmap table coverage
                When None, uses standard PostScript name matching.

        Returns:
            New FontInfo instance with resolved metadata, or None if font not found.
            The original FontInfo instance is not modified (immutable pattern).

        Note:
            Generic family (sans-serif, serif, monospace) is not included in the
            returned FontInfo. Determining the generic family automatically is
            non-trivial and would require font classification heuristics or
            external databases.

        Example:
            >>> # Standard resolution
            >>> font = FontInfo.find('ArialMT')
            >>> resolved = font.resolve()
            >>>
            >>> # Charset-based resolution
            >>> codepoints = {0x3042, 0x3044, 0x3046}  # Japanese hiragana
            >>> resolved = font.resolve(charset_codepoints=codepoints)
        """
        # If font already has a valid file path, no need to resolve
        if self.file and os.path.exists(self.file):
            logger.debug(
                f"Font '{self.postscript_name}' already has valid file path: {self.file}"
            )
            return self

        # Try platform-specific resolution
        if HAS_FONTCONFIG:
            # Linux/macOS: Use fontconfig with CharSet support
            return self._resolve_fontconfig(charset_codepoints)
        elif HAS_WINDOWS_FONTS:
            # Windows: Use registry + cmap checking
            return self._resolve_windows(charset_codepoints)
        else:
            logger.debug(
                f"Cannot resolve font '{self.postscript_name}': "
                "no font resolution system available"
            )
            return None

    def _resolve_fontconfig(self, charset_codepoints: set[int] | None) -> Self | None:
        """Resolve font using fontconfig (Linux/macOS)."""
        logger.debug(f"Resolving font '{self.postscript_name}' via fontconfig")

        try:
            if charset_codepoints is not None:
                # Charset-based resolution
                logger.debug(
                    f"Using charset with {len(charset_codepoints)} codepoints "
                    f"for '{self.postscript_name}'"
                )

                # Create CharSet from codepoints
                charset = fontconfig.CharSet.from_codepoints(sorted(charset_codepoints))

                # Use properties dict for charset-based matching
                # Cannot specify both 'pattern' and 'properties' in fontconfig API
                match = fontconfig.match(
                    properties={
                        "postscriptname": self.postscript_name,
                        "charset": charset,
                    },
                    select=("file", "family", "style", "weight"),
                )
            else:
                # Standard PostScript name matching (existing behavior)
                match = fontconfig.match(
                    pattern=f":postscriptname={self.postscript_name}",
                    select=("file", "family", "style", "weight"),
                )

            if not match or not match.get("file"):
                logger.debug(f"Font '{self.postscript_name}' not found via fontconfig")
                return None

            # Create new FontInfo with resolved metadata
            resolved = FontInfo(
                postscript_name=self.postscript_name,
                file=str(match["file"]),  # type: ignore
                family=str(match["family"]),  # type: ignore
                style=str(match["style"]),  # type: ignore
                weight=float(match["weight"]),  # type: ignore
            )

            # Log if font substitution occurred
            if resolved.family != self.family:
                logger.info(
                    f"Font substitution: '{self.family}' → '{resolved.family}' "
                    f"(file: {resolved.file})"
                )
            else:
                logger.debug(
                    f"Font '{self.postscript_name}' resolved to same family "
                    f"'{resolved.family}' (file: {resolved.file})"
                )

            return resolved

        except Exception as e:
            # Graceful degradation: fall back to name matching
            if charset_codepoints is not None:
                logger.warning(
                    f"Charset-based resolution failed for '{self.postscript_name}': {e}. "
                    "Falling back to name-only matching"
                )
                return self.resolve(charset_codepoints=None)

            logger.warning(f"Font resolution failed for '{self.postscript_name}': {e}")
            return None

    def _resolve_windows(self, charset_codepoints: set[int] | None) -> Self | None:
        """Resolve font using Windows registry (Windows only)."""
        logger.debug(f"Resolving font '{self.postscript_name}' via Windows registry")

        try:
            resolver = _windows_fonts.get_windows_font_resolver()  # type: ignore[attr-defined]

            if charset_codepoints is not None:
                logger.debug(
                    f"Resolving '{self.postscript_name}' on Windows "
                    f"with {len(charset_codepoints)} codepoints"
                )
                match = resolver.find_with_charset(
                    self.postscript_name, charset_codepoints
                )
            else:
                match = resolver.find(self.postscript_name)

            if not match:
                logger.debug(
                    f"Font '{self.postscript_name}' not found via Windows registry"
                )
                return None

            # Create resolved FontInfo
            resolved = FontInfo(
                postscript_name=self.postscript_name,
                file=str(match["file"]),
                family=str(match["family"]),
                style=str(match["style"]),
                weight=float(match["weight"]),
            )

            # Log substitution
            if resolved.family != self.family:
                logger.info(
                    f"Font substitution: '{self.family}' → '{resolved.family}' "
                    f"(file: {resolved.file})"
                )
            else:
                logger.debug(
                    f"Font '{self.postscript_name}' resolved to same family "
                    f"'{resolved.family}' (file: {resolved.file})"
                )

            return resolved

        except Exception as e:
            # Graceful degradation: fall back to name matching
            if charset_codepoints is not None:
                logger.warning(
                    f"Charset-based resolution failed for '{self.postscript_name}': {e}. "
                    "Falling back to name-only matching"
                )
                return self.resolve(charset_codepoints=None)

            logger.warning(f"Font resolution failed for '{self.postscript_name}': {e}")
            return None

    @staticmethod
    def _find_via_fontconfig(
        postscriptname: str, charset_codepoints: set[int] | None
    ) -> Self | None:
        """Find font via fontconfig with optional charset matching.

        Args:
            postscriptname: PostScript name of the font.
            charset_codepoints: Optional set of Unicode codepoints for charset matching.

        Returns:
            FontInfo object if found, None otherwise.
        """
        logger.debug(
            f"Font '{postscriptname}' not in static mapping, trying fontconfig..."
        )

        try:
            if charset_codepoints is not None:
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
        except Exception as e:
            # Graceful degradation: fall back to name-only matching
            if charset_codepoints is not None:
                logger.warning(
                    f"Charset-based matching failed for '{postscriptname}': {e}. "
                    "Falling back to name-only matching"
                )
                match = fontconfig.match(
                    pattern=f":postscriptname={postscriptname}",
                    select=("file", "family", "style", "weight"),
                )
            else:
                # If name-only matching also failed, re-raise
                raise

        if match:
            logger.info(
                f"Resolved '{postscriptname}' via fontconfig fallback: "
                f"{match['family']}"
            )
            return FontInfo(
                postscript_name=postscriptname,
                file=match["file"],  # type: ignore
                family=match["family"],  # type: ignore
                style=match["style"],  # type: ignore
                weight=match["weight"],  # type: ignore
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

        Returns:
            FontInfo object if found, None otherwise.
        """
        logger.debug(
            f"Font '{postscriptname}' not in static mapping, "
            "trying Windows registry..."
        )
        resolver = _windows_fonts.get_windows_font_resolver()  # type: ignore[attr-defined]

        try:
            if charset_codepoints is not None:
                # Use charset-based matching
                logger.debug(
                    f"Using charset with {len(charset_codepoints)} codepoints "
                    f"for '{postscriptname}'"
                )
                match = resolver.find_with_charset(postscriptname, charset_codepoints)
            else:
                # Standard PostScript name matching
                match = resolver.find(postscriptname)
        except Exception as e:
            # Graceful degradation: fall back to name-only matching
            if charset_codepoints is not None:
                logger.warning(
                    f"Charset-based matching failed for '{postscriptname}': {e}. "
                    "Falling back to name-only matching"
                )
                match = resolver.find(postscriptname)
            else:
                # If name-only matching also failed, re-raise
                raise

        if match:
            logger.info(
                f"Resolved '{postscriptname}' via Windows registry fallback: "
                f"{match['family']}"
            )
            return FontInfo(
                postscript_name=postscriptname,
                file=str(match["file"]),
                family=str(match["family"]),
                style=str(match["style"]),
                weight=float(match["weight"]),
            )

        return None

    @staticmethod
    def find(
        postscriptname: str,
        font_mapping: dict[str, dict[str, float | str]] | None = None,
        enable_fontconfig: bool = True,
        charset_codepoints: set[int] | None = None,
    ) -> Self | None:
        """Find font information by PostScript name.

        This method tries multiple strategies to resolve the font:
        1. Try custom font mapping if provided (takes priority)
        2. Try static font mapping (fast, deterministic, cross-platform)
        3. Fall back to platform-specific resolution with optional charset matching:
           - Linux/macOS: fontconfig (if enabled)
           - Windows: Registry + fontTools parsing

        Args:
            postscriptname: PostScript name of the font (e.g., "ArialMT").
            font_mapping: Optional custom font mapping dictionary. Takes priority
                         over default mapping. Format:
                         {"PostScriptName": {"family": str, "style": str, "weight": float}}
            enable_fontconfig: If True, fall back to platform-specific resolution
                              for fonts not in static mapping. If False, only use
                              static/custom mapping. Default: True.
            charset_codepoints: Optional set of Unicode codepoints for charset-based
                               font matching. Only used during platform-specific fallback
                               (tier 3) when font is not found in static mapping. When
                               provided, prioritizes fonts with better glyph coverage
                               for the specified characters. Gracefully falls back to
                               name-only matching on errors. Default: None.

        Returns:
            FontInfo object with font metadata, or None if font not found.

        Note:
            Static mapping provides family/style/weight but no file path. This is
            sufficient for SVG text rendering. Font embedding requires platform-
            specific resolution (fontconfig or Windows registry) to locate the
            actual font files on the system.

            Charset matching is only applied during platform-specific fallback when
            the font is not found in custom or static mapping. This preserves the
            performance benefit of static mapping for common fonts while improving
            resolution success rate for fonts not in the static mapping.

        Example:
            >>> # Standard resolution (fast for fonts in static mapping)
            >>> font = FontInfo.find('ArialMT')
            >>>
            >>> # With charset matching for better fallback
            >>> codepoints = {0x3042, 0x3044, 0x3046}  # Japanese hiragana
            >>> font = FontInfo.find('NotoSansCJK-Regular', charset_codepoints=codepoints)
        """
        mapping_data = _font_mapping.find_in_mapping(postscriptname, font_mapping)
        if mapping_data:
            logger.debug(
                f"Resolved '{postscriptname}' via static font mapping: "
                f"{mapping_data['family']}"
            )
            return FontInfo(
                postscript_name=postscriptname,
                file="",  # No file path available from static mapping
                family=str(mapping_data["family"]),
                style=str(mapping_data["style"]),
                weight=float(mapping_data["weight"]),
            )

        # Fall back to platform-specific resolution for fonts not in static mapping
        if enable_fontconfig:
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

        # Font not found in any mapping
        if not enable_fontconfig:
            logger.warning(
                f"Font '{postscriptname}' not found in static font mapping "
                "(platform-specific lookup disabled). "
                "Text will be converted without font-family attribute. "
                "Consider providing a custom font mapping via the font_mapping parameter."
            )
        elif not HAS_FONTCONFIG and not HAS_WINDOWS_FONTS:
            logger.warning(
                f"Font '{postscriptname}' not found in static font mapping "
                "(platform-specific resolution not available). "
                "Text will be converted without font-family attribute. "
                "Consider providing a custom font mapping via the font_mapping parameter."
            )
        else:
            platform_name = "fontconfig" if HAS_FONTCONFIG else "Windows registry"
            logger.warning(
                f"Font '{postscriptname}' not found via static mapping or {platform_name}. "
                "Text will be converted without font-family attribute. "
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
    subset_chars: set[str] | None = None,
    font_format: str = "ttf",
) -> str:
    """Encode a font file as a data URI with optional subsetting and caching.

    This helper consolidates the logic for encoding fonts with subsetting
    support and cache management.

    Args:
        font_path: Path to the font file.
        cache: Dictionary to use for caching encoded data URIs.
        subset_chars: Optional set of characters to subset the font to.
            If None, the full font is encoded.
        font_format: Font format for output: "ttf", "otf", or "woff2".

    Returns:
        Data URI string for the encoded font.

    Raises:
        ImportError: If subsetting is requested but fonttools is not available.
        FileNotFoundError: If font file doesn't exist.
        IOError: If font file can't be read.

    Note:
        - Cache keys include format and character count for subset fonts
        - Full fonts use just the file path as cache key
        - Missing characters trigger fallback to full font with warning
    """
    # Subsetting path
    if subset_chars:
        # Create cache key for subset fonts (include format and char count)
        cache_key = f"{font_path}:{font_format}:{len(subset_chars)}"

        if cache_key not in cache:
            logger.debug(
                f"Subsetting font: {font_path} -> {font_format} "
                f"({len(subset_chars)} chars)"
            )
            try:
                font_bytes = font_subsetting.subset_font(  # type: ignore
                    input_path=font_path,
                    output_format=font_format,
                    unicode_chars=subset_chars,
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


def create_charset_codepoints(chars: set[str]) -> set[int] | None:
    """Create set of Unicode codepoints from characters.

    This function converts a set of Unicode characters to a set of
    integer codepoints suitable for charset-based font matching.

    Args:
        chars: Set of Unicode characters (e.g., {"A", "あ", "中"}).

    Returns:
        Set of Unicode codepoints (integers), or None if chars is empty.
        Multi-codepoint characters (emoji with modifiers) are split into
        individual codepoints.

    Example:
        >>> chars = {"H", "e", "l", "o"}
        >>> codepoints = create_charset_codepoints(chars)
        >>> codepoints
        {72, 101, 108, 111}
    """
    if not chars:
        return None

    from psd2svg.font_subsetting import _chars_to_unicode_list

    # Reuse existing conversion logic
    codepoint_list = _chars_to_unicode_list(chars)
    codepoint_set = set(codepoint_list)

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
