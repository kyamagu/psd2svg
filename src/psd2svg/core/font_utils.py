import base64
import dataclasses
import logging
import os

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self

try:
    import fontconfig

    HAS_FONTCONFIG = True
except ImportError:
    HAS_FONTCONFIG = False

# Import font_subsetting conditionally to avoid import errors when fonttools not installed
try:
    from psd2svg import font_subsetting as _font_subsetting

    HAS_FONT_SUBSETTING = True
except ImportError:
    HAS_FONT_SUBSETTING = False
    _font_subsetting = None  # type: ignore

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

    def get_font_file(self) -> str | None:
        """Get the font file path, querying fontconfig if necessary.

        If the font file path is empty (e.g., from static mapping), this method
        attempts to query fontconfig to find the font file on the system.

        Returns:
            Font file path, or None if font file cannot be located.

        Example:
            >>> font_info = FontInfo.find('ArialMT')  # May have empty file path
            >>> font_path = font_info.get_font_file()  # Queries fontconfig if needed
            >>> if font_path:
            ...     data_uri = encode_font_data_uri(font_path)
        """
        # Return existing file path if available
        if self.file:
            return self.file

        # Try fontconfig fallback if available
        if not HAS_FONTCONFIG:
            logger.debug(
                f"Font '{self.postscript_name}' has no file path and "
                "fontconfig is not available"
            )
            return None

        logger.debug(
            f"Font '{self.postscript_name}' has no file path, "
            "querying fontconfig for fallback"
        )

        try:
            match = fontconfig.match(
                pattern=f":postscriptname={self.postscript_name}",
                select=("file",),
            )
            if match and match.get("file"):
                font_path: str = match["file"]  # type: ignore
                logger.info(
                    f"Found font file via fontconfig fallback: {font_path}"
                )
                return font_path
            else:
                logger.debug(
                    f"Font '{self.postscript_name}' not found via "
                    "fontconfig fallback"
                )
                return None
        except Exception as e:
            logger.warning(
                f"Fontconfig fallback failed for '{self.postscript_name}': {e}"
            )
            return None

    @staticmethod
    def find(
        postscriptname: str,
        font_mapping: dict[str, dict[str, float | str]] | None = None,
    ) -> Self | None:
        """Find font information by PostScript name.

        This method tries multiple strategies to resolve the font:
        1. Try static font mapping first (fast, deterministic, cross-platform)
        2. Fall back to fontconfig if available (provides file path for embedding)
        3. Check custom font mapping if provided (takes priority over default mapping)

        Args:
            postscriptname: PostScript name of the font (e.g., "ArialMT").
            font_mapping: Optional custom font mapping dictionary. Takes priority
                         over default mapping. Format:
                         {"PostScriptName": {"family": str, "style": str, "weight": float}}

        Returns:
            FontInfo object with font metadata, or None if font not found.

        Note:
            Static mapping provides family/style/weight but no file path. This is
            sufficient for SVG text rendering. Font embedding requires fontconfig
            to locate the actual font files on the system.
        """
        # Try static font mapping first - fast, deterministic, cross-platform
        from psd2svg.core import font_mapping as fm

        mapping_data = fm.find_in_mapping(postscriptname, font_mapping)
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

        # Fall back to fontconfig (if available) for fonts not in static mapping
        if HAS_FONTCONFIG:
            logger.debug(
                f"Font '{postscriptname}' not in static mapping, trying fontconfig..."
            )
            match = fontconfig.match(
                pattern=f":postscriptname={postscriptname}",
                select=("file", "family", "style", "weight"),
            )
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

        # Font not found in any mapping
        if not HAS_FONTCONFIG:
            logger.warning(
                f"Font '{postscriptname}' not found in static font mapping. "
                "Text layer will be rasterized. Consider providing a custom font mapping "
                "via the font_mapping parameter."
            )
        else:
            logger.warning(
                f"Font '{postscriptname}' not found via static mapping or fontconfig. "
                "Text layer will be rasterized. Make sure the font is installed on your "
                "system, or provide a custom font mapping via the font_mapping parameter."
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
        # Check if font_subsetting is available
        if not HAS_FONT_SUBSETTING:
            raise ImportError(
                "Font subsetting requires fonttools package. "
                "Install with: uv sync --group fonts"
            )

        # Create cache key for subset fonts (include format and char count)
        cache_key = f"{font_path}:{font_format}:{len(subset_chars)}"

        if cache_key not in cache:
            logger.debug(
                f"Subsetting font: {font_path} -> {font_format} "
                f"({len(subset_chars)} chars)"
            )
            try:
                font_bytes = _font_subsetting.subset_font(  # type: ignore
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
