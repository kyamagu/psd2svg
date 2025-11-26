import dataclasses
import logging

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self

import fontconfig

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

    @staticmethod
    def find(postscriptname: str) -> Self | None:
        """Find the font family name for the given span index."""
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
