# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

# https://helpx.adobe.com/photoshop/using/blending-modes.html
BLEND_MODE = {
    b'pass': 'normal /*pass*/',
    b'norm': 'normal',
    b'diss': 'normal /*dissolve*/',
    b'dark': 'darken',
    b'mul ': 'multiply',
    b'idiv': 'color-burn',
    b'lbrn': 'plus-darker /*linear-burn*/',  # Only webkit
    b'dkCl': 'darken /*darker-color*/',
    b'lite': 'lighten',
    b'scrn': 'screen',
    b'div ': 'color-dodge',
    b'lddg': 'plus-lighter /*linear-dodge*/',  # Only webkit
    b'lgCl': 'lighten /*lighter-color*/',
    b'over': 'overlay',
    b'sLit': 'soft-light',
    b'hLit': 'hard-light',
    b'vLit': 'lighten /*vivid-light*/',
    b'lLit': 'darken /*linear-light*/',
    b'pLit': 'normal /*pin-light*/',
    b'hMix': 'normal /*hard-mix*/',
    b'diff': 'difference',
    b'smud': 'exclusion',
    b'fsub': 'difference /*subtract*/',
    b'hue ': 'hue',
    b'sat ': 'saturation',
    b'colr': 'color',
    b'lum ': 'luminosity',
}

BLEND_MODE2 = {
    b'Nrml': 'normal',
    b'Dslv': 'normal /*dissolve*/',
    b'Drkn': 'darken',
    b'Mltp': 'multiply',
    b'CBrn': 'color-burn',
    b'linearBurn': 'plus-darker /*linear-burn*/',  # Only webkit
    b'darkerColor': 'darken',
    b'Lghn': 'lighten',
    b'Scrn': 'screen',
    b'CDdg': 'color-dodge',
    b'linearDodge': 'plus-lighter /*linear-dodge*/',  # Only webkit
    b'lighterColor': 'lighten /*lighter-color*/',
    b'Ovrl': 'overlay',
    b'SftL': 'soft-light',
    b'HrdL': 'hard-light',
    b'vividLight': 'lighten /*vivid-light*/',
    b'linearLight': 'darken /*linear-light*/',
    b'pinLight': 'normal /*pin-light*/',
    b'hardMix': 'normal /*hard-mix*/',
    b'Dfrn': 'difference',
    b'Xclu': 'exclusion',
    b'blendSubtraction': 'difference /*subtract*/',
    b'blendDivide': 'soft-light /*divide*/',
    b'H   ': 'hue',
    b'Strt': 'saturation',
    b'Clr ': 'color',
    b'Lmns': 'luminosity',
}

JUSTIFICATIONS = {
    0: 'start',
    1: 'end',
    2: 'middle',
}
