import re
from logging import getLogger
from re import Pattern

logger = getLogger(__name__)

ILLEGAL_XML_RE: Pattern[str] = re.compile(
    "[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf\ufffe-\uffff]"
)


def safe_utf8(text: str) -> str:
    return ILLEGAL_XML_RE.sub(" ", text)
