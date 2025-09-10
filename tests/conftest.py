import logging
import os

logger = logging.getLogger(__name__)


def get_fixture(name: str) -> str:
    """Get a fixture by name."""
    return os.path.join(os.path.dirname(__file__), "fixtures", name)


ADJUSTMENTS = [
    "layer-types/black-and-white.psd",
    "layer-types/brightness-contrast.psd",
    "layer-types/channel-mixer.psd",
    "layer-types/color-balance.psd",
    "layer-types/curves-with-vectormask.psd",
    "layer-types/curves.psd",
    "layer-types/exposure.psd",
    "layer-types/gradient-map-v3-classic.psd",
    "layer-types/gradient-map-v3-linear.psd",
    "layer-types/gradient-map.psd",
    "layer-types/hue-saturation.psd",
    "layer-types/invert.psd",
    "layer-types/levels.psd",
    "layer-types/photo-filter.psd",
    "layer-types/selective-color.psd",
    "layer-types/threshold.psd",
    "layer-types/vibrance.psd",
]

FILLS = [
    "layer-types/gradient-fill.psd",
    "layer-types/solid-color-fill.psd",
    "layer-types/pattern-fill.psd",
]

TYPES = [
    "layer-types/group.psd",
    "layer-types/pixel-layer.psd",
    "layer-types/shape-layer.psd",
    "layer-types/smartobject-layer.psd",
    "layer-types/type-layer.psd",
]

ALL = ADJUSTMENTS + FILLS + TYPES