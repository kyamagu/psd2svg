import logging
from typing import Sequence

from psd_tools.psd.descriptor import Descriptor
from psd_tools.terminology import Klass, Enum

logger = logging.getLogger(__name__)


def cmyk2rgb(values: Sequence[float]) -> tuple[int, int, int]:
    """Convert CMYK color to RGB color."""
    assert len(values) == 4
    return (
        clip_int(2.55 * (1.0 - values[0]) * (1.0 - values[3])),
        clip_int(2.55 * (1.0 - values[1]) * (1.0 - values[3])),
        clip_int(2.55 * (1.0 - values[2]) * (1.0 - values[3])),
    )


def descriptor2hex(desc: Descriptor, fallback: str = "transparent") -> str:
    """Convert a color descriptor to an RGB hex string."""

    if desc.classID == Klass.RGBColor:
        if Enum.Red in desc:
            r = desc.get(Enum.Red, 0)
            g = desc.get(Enum.Green, 0)
            b = desc.get(Enum.Blue, 0)
            return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        elif "redFloat" in desc:
            r = float2uint8(desc.get("redFloat", 0))
            g = float2uint8(desc.get("greenFloat", 0))
            b = float2uint8(desc.get("blueFloat", 0))
            return f"#{r:02x}{g:02x}{b:02x}"
        else:
            raise ValueError(f"Unsupported RGB color format: {desc}")

    if desc.classID == Klass.CMYKColor:
        c = desc.get(Enum.Cyan, 0)
        m = desc.get(Enum.Magenta, 0)
        y = desc.get(Enum.Yellow, 0)
        k = desc.get(Enum.Black, 0)
        r, g, b = cmyk2rgb((c / 100, m / 100, y / 100, k / 100))
        return f"#{r:02x}{g:02x}{b:02x}"

    if desc.classID == Klass.Grayscale:
        gray = desc.get(Enum.Gray, 0)
        assert isinstance(gray, float)
        gray = float2uint8(gray)
        return f"#{gray:02x}{gray:02x}{gray:02x}"

    logger.warning("Unsupported color mode: %s", desc.classID)
    return fallback


def float2uint8(v: float) -> int:
    """Convert a float in the range [0.0, 1.0] to an integer in the range [0, 255]."""
    return clip_int(255 * v)


def clip_int(value: int | float, min_value: int = 0, max_value: int = 255) -> int:
    """Clip an int value to the specified range."""
    return max(min_value, min(max_value, int(value)))
