# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from logging import getLogger

logger = getLogger(__name__)


def cmyk2rgb(cmyk):
    return (2.55 * (1.0 - cmyk[0]) * (1.0 - cmyk[3]),
            2.55 * (1.0 - cmyk[1]) * (1.0 - cmyk[3]),
            2.55 * (1.0 - cmyk[2]) * (1.0 - cmyk[3]))
