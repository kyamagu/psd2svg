# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from psd_tools.constants import BlendMode, BlendMode2

# https://helpx.adobe.com/photoshop/using/blending-modes.html
BLEND_MODE = {
    # Layer modes.
    BlendMode.PASS_THROUGH: 'normal /*pass*/',
    BlendMode.NORMAL: 'normal',
    BlendMode.DISSOLVE: 'normal /*dissolve*/',
    BlendMode.DARKEN: 'darken',
    BlendMode.MULTIPLY: 'multiply',
    BlendMode.COLOR_BURN: 'color-burn',
    BlendMode.LINEAR_BURN: 'plus-darker /*linear-burn*/',  # Only webkit
    BlendMode.DARKER_COLOR: 'darken /*darker-color*/',
    BlendMode.LIGHTEN: 'lighten',
    BlendMode.SCREEN: 'screen',
    BlendMode.COLOR_DODGE: 'color-dodge',
    BlendMode.LINEAR_DODGE: 'plus-lighter /*linear-dodge*/',  # Only webkit
    BlendMode.LIGHTER_COLOR: 'lighten /*lighter-color*/',
    BlendMode.OVERLAY: 'overlay',
    BlendMode.SOFT_LIGHT: 'soft-light',
    BlendMode.HARD_LIGHT: 'hard-light',
    BlendMode.VIVID_LIGHT: 'lighten /*vivid-light*/',
    BlendMode.LINEAR_LIGHT: 'darken /*linear-light*/',
    BlendMode.PIN_LIGHT: 'normal /*pin-light*/',
    BlendMode.HARD_MIX: 'normal /*hard-mix*/',
    BlendMode.DIFFERENCE: 'difference',
    BlendMode.EXCLUSION: 'exclusion',
    BlendMode.SUBTRACT: 'difference /*subtract*/',
    BlendMode.DIVIDE: 'difference /*divide*/',
    BlendMode.HUE: 'hue',
    BlendMode.SATURATION: 'saturation',
    BlendMode.COLOR: 'color',
    BlendMode.LUMINOSITY: 'luminosity',
    # Descriptor-based modes.
    BlendMode2.NORMAL: 'normal',
    BlendMode2.DISSOLVE: 'normal /*dissolve*/',
    BlendMode2.DARKEN: 'darken',
    BlendMode2.MULTIPLY: 'multiply',
    BlendMode2.COLOR_BURN: 'color-burn',
    BlendMode2.LINEAR_BURN: 'plus-darker /*linear-burn*/',  # Only webkit
    BlendMode2.DARKER_COLOR: 'darken /*darker-color*/',
    BlendMode2.LIGHTEN: 'lighten',
    BlendMode2.SCREEN: 'screen',
    BlendMode2.COLOR_DODGE: 'color-dodge',
    BlendMode2.LINEAR_DODGE: 'plus-lighter /*linear-dodge*/',  # Only webkit
    BlendMode2.LIGHTER_COLOR: 'lighten /*lighter-color*/',
    BlendMode2.OVERLAY: 'overlay',
    BlendMode2.SOFT_LIGHT: 'soft-light',
    BlendMode2.HARD_LIGHT: 'hard-light',
    BlendMode2.VIVID_LIGHT: 'lighten /*vivid-light*/',
    BlendMode2.LINEAR_LIGHT: 'darken /*linear-light*/',
    BlendMode2.PIN_LIGHT: 'normal /*pin-light*/',
    BlendMode2.HARD_MIX: 'normal /*hard-mix*/',
    BlendMode2.DIFFERENCE: 'difference',
    BlendMode2.EXCLUSION: 'exclusion',
    BlendMode2.SUBTRACT: 'difference /*subtract*/',
    BlendMode2.DIVIDE: 'difference /*divide*/',
    BlendMode2.HUE: 'hue',
    BlendMode2.SATURATION: 'saturation',
    BlendMode2.COLOR: 'color',
    BlendMode2.LUMINOSITY: 'luminosity',
}

JUSTIFICATIONS = {
    0: 'start',
    1: 'end',
    2: 'middle',
}
