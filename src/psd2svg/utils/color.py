import logging
from typing import Sequence

logger = logging.getLogger(__name__)


def cmyk2rgb(values: Sequence[float]) -> tuple[float, float, float]:
    """Convert CMYK color to RGB color."""
    assert len(values) == 4
    return (
        2.55 * (1.0 - values[0]) * (1.0 - values[3]),
        2.55 * (1.0 - values[1]) * (1.0 - values[3]),
        2.55 * (1.0 - values[2]) * (1.0 - values[3]),
    )
