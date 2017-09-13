# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from logging import getLogger
import re

logger = getLogger(__name__)

ILLEGAL_XML_RE = re.compile(
    '[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf'
    '\ufffe-\uffff]')


def safe_utf8(text):
    return ILLEGAL_XML_RE.sub(' ', text)
