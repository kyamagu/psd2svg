import logging
from typing import Sequence

from psd_tools.psd.descriptor import Descriptor
from psd_tools.terminology import Klass, Enum

logger = logging.getLogger(__name__)


def cmyk2rgb(values: Sequence[float]) -> tuple[float, float, float]:
    """Convert CMYK color to RGB color."""
    assert len(values) == 4
    return (
        2.55 * (1.0 - values[0]) * (1.0 - values[3]),
        2.55 * (1.0 - values[1]) * (1.0 - values[3]),
        2.55 * (1.0 - values[2]) * (1.0 - values[3]),
    )


def descriptor2hex(desc: Descriptor, fallback: str = "transparent") -> str:
    """Convert a color descriptor to an RGB hex string."""
    if desc.classID == Klass.RGBColor:
        r = desc.get(Enum.Red, 0)
        g = desc.get(Enum.Green, 0)
        b = desc.get(Enum.Blue, 0)
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
    if desc.classID == Klass.CMYKColor:
        c = desc.get(Enum.Cyan, 0)
        m = desc.get(Enum.Magenta, 0)
        y = desc.get(Enum.Yellow, 0)
        k = desc.get(Enum.Black, 0)
        r, g, b = cmyk2rgb((c / 100, m / 100, y / 100, k / 100))
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
    if desc.classID == Klass.GrayColor:
        gray = desc.get(Enum.Gray, 0)
        gray = int(2.55 * gray)
        return f"#{gray:02x}{gray:02x}{gray:02x}"
    logger.warning("Unsupported color mode: %s", desc.classID)
    return fallback
