import dataclasses
import logging

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self

try:
    import fontconfig

    HAS_FONTCONFIG = True
except ImportError:
    HAS_FONTCONFIG = False

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

    @staticmethod
    def find(postscriptname: str) -> Self | None:
        """Find the font family name for the given span index."""
        if not HAS_FONTCONFIG:
            logger.warning(
                "fontconfig-py is not available. Text layer conversion is disabled. "
                "On Windows, fontconfig is not available - text layers will be rasterized. "
                "On Linux/macOS, ensure fontconfig-py is installed."
            )
            return None

        match = fontconfig.match(
            pattern=f":postscriptname={postscriptname}",
            select=("file", "family", "style", "weight"),
        )
        if not match:
            logger.warning(
                f"Font file for '{postscriptname}' not found. "
                "Make sure the font is installed on your system."
            )
            return None
        return FontInfo(
            postscript_name=postscriptname,
            file=match["file"],  # type: ignore
            family=match["family"],  # type: ignore
            style=match["style"],  # type: ignore
            weight=match["weight"],  # type: ignore
        )
