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
    Enum.Normal: "normal",
    Enum.Dissolve: "normal",
    Enum.Darken: "darken",
    Enum.Multiply: "multiply",
    Enum.ColorBurn: "color-burn",
    b"linearBurn": "plus-darker",
    # darker-color?
    Enum.Lighten: "lighten",
    Enum.Screen: "screen",
    Enum.ColorDodge: "color-dodge",
    b"linearDodge": "plus-lighter",
    # lighter-color?
    Enum.Overlay: "overlay",
    Enum.SoftLight: "soft-light",
    Enum.HardLight: "hard-light",
    # vivid-light?
    # linear-light?
    # pin-light?
    # hard-mix?
    Enum.Difference: "difference",
    Enum.Exclusion: "exclusion",
    Enum.Subtract: "difference",
    # divide?
    Enum.Hue: "hue",
    Enum.Saturation: "saturation",
    Enum.Color: "color",
    Enum.Luminosity: "luminosity",
}