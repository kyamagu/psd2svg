from collections.abc import Sequence
from logging import getLogger
from typing import Tuple

logger = getLogger(__name__)


def cmyk2rgb(cmyk: Sequence[float]) -> Tuple[float, float, float]:
    return (
        2.55 * (1.0 - cmyk[0]) * (1.0 - cmyk[3]),
        2.55 * (1.0 - cmyk[1]) * (1.0 - cmyk[3]),
        2.55 * (1.0 - cmyk[2]) * (1.0 - cmyk[3]),
    )
