from typing import Union

from psd_tools.constants import BlendMode
from psd_tools.terminology import Enum

# https://helpx.adobe.com/photoshop/using/blending-modes.html
BLEND_MODE: dict[Union[BlendMode, bytes], str] = {
    # Layer modes.
    BlendMode.PASS_THROUGH: "pass-through",
    BlendMode.NORMAL: "normal",
    BlendMode.DISSOLVE: "normal",
    BlendMode.DARKEN: "darken",
    BlendMode.MULTIPLY: "multiply",
    BlendMode.COLOR_BURN: "color-burn",
    BlendMode.LINEAR_BURN: "plus-darker",
    BlendMode.DARKER_COLOR: "darken",
    BlendMode.LIGHTEN: "lighten",
    BlendMode.SCREEN: "screen",
    BlendMode.COLOR_DODGE: "color-dodge",
    BlendMode.LINEAR_DODGE: "plus-lighter",
    BlendMode.LIGHTER_COLOR: "lighten",
    BlendMode.OVERLAY: "overlay",
    BlendMode.SOFT_LIGHT: "soft-light",
    BlendMode.HARD_LIGHT: "hard-light",
    BlendMode.VIVID_LIGHT: "lighten",
    BlendMode.LINEAR_LIGHT: "darken",
    BlendMode.PIN_LIGHT: "normal",
    BlendMode.HARD_MIX: "normal",
    BlendMode.DIFFERENCE: "difference",
    BlendMode.EXCLUSION: "exclusion",
    BlendMode.SUBTRACT: "difference",
    BlendMode.DIVIDE: "difference",
    BlendMode.HUE: "hue",
    BlendMode.SATURATION: "saturation",
    BlendMode.COLOR: "color",
    BlendMode.LUMINOSITY: "luminosity",
    # Descriptor values.
    # TODO: Check bytes values.
    Enum.Normal: "normal",
    Enum.Dissolve: "normal",
    Enum.Darken: "darken",
    Enum.Multiply: "multiply",
    Enum.ColorBurn: "color-burn",
    b"linearBurn": "plus-darker",
    b"darkerColor": "darken",
    Enum.Lighten: "lighten",
    Enum.Screen: "screen",
    Enum.ColorDodge: "color-dodge",
    b"linearDodge": "plus-lighter",
    b"lighterColor": "lighten",
    Enum.Overlay: "overlay",
    Enum.SoftLight: "soft-light",
    Enum.HardLight: "hard-light",
    b"vividLight": "lighten",
    b"linearLight": "darken",
    b"pinLight": "normal",
    b"hardMix": "normal",
    Enum.Difference: "difference",
    Enum.Exclusion: "exclusion",
    Enum.Subtract: "difference",
    b"divide": "difference",
    Enum.Hue: "hue",
    Enum.Saturation: "saturation",
    Enum.Color: "color",
    Enum.Luminosity: "luminosity",
}

# Blend modes that are not accurately supported in SVG and are mapped to approximations.
# These will trigger warnings when used.
INACCURATE_BLEND_MODES: set[Union[BlendMode, bytes]] = {
    # Dissolve mode uses random pixel patterns, not supported in SVG
    BlendMode.DISSOLVE,
    Enum.Dissolve,
    # Linear burn uses plus-darker which has limited browser support
    BlendMode.LINEAR_BURN,
    b"linearBurn",
    # Linear dodge uses plus-lighter which has limited browser support
    BlendMode.LINEAR_DODGE,
    b"linearDodge",
    # Darker/Lighter Color modes compare color values, approximated with darken/lighten
    BlendMode.DARKER_COLOR,
    b"darkerColor",
    BlendMode.LIGHTER_COLOR,
    b"lighterColor",
    # Advanced light modes approximated with simpler modes
    BlendMode.VIVID_LIGHT,
    b"vividLight",
    BlendMode.LINEAR_LIGHT,
    b"linearLight",
    BlendMode.PIN_LIGHT,
    b"pinLight",
    BlendMode.HARD_MIX,
    b"hardMix",
    # Subtract and Divide modes approximated with difference
    BlendMode.SUBTRACT,
    Enum.Subtract,
    BlendMode.DIVIDE,
    b"divide",
}
