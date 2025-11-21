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
        family: List of family names.
        style: List of style names in different languages.
        weight: List of weight values. 80.0 is regular and 200.0 is bold.
    """

    postscript_name: str
    family: list[str]
    style: list[str]
    weight: list[int]

    @property
    def family_name(self) -> str:
        """Get the primary family name."""
        return self.family[0] if self.family else ""
    
    @property
    def bold(self) -> bool:
        """Whether the font is bold."""
        # TODO: Should we consider style names as well?
        return any(w >= 200 for w in self.weight)
    
    @property
    def italic(self) -> bool:
        """Whether the font is italic."""
        return any("italic" in s.lower() for s in self.style)

    @staticmethod
    def find(postscriptname: str) -> Self | None:
        """Find the font family name for the given span index."""
        results = fontconfig.query(
            where=f":postscriptname={postscriptname}",
            select=("family", "style", "weight"),
        )
        if not results:
            logger.warning(
                f"Font file for '{postscriptname}' not found. "
                "Make sure the font is installed on your system."
            )
            return None
        return FontInfo(
            postscript_name=postscriptname,
            family=results[0]["family"],  # type: ignore
            style=results[0]["style"],  # type: ignore
            weight=results[0]["weight"],  # type: ignore
        )