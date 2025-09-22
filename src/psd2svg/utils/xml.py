import re
from logging import getLogger
from re import Pattern

logger = getLogger(__name__)

ILLEGAL_XML_RE: Pattern[str] = re.compile(
    "[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf\ufffe-\uffff]"
)


def safe_utf8(text: str) -> str:
    """Remove illegal XML characters from text."""
    return ILLEGAL_XML_RE.sub(" ", text)


def num2str(num: int | float | bool, format = "g") -> str:
    """Convert a number to a string, using the specified format for floats."""
    if isinstance(num, bool):
        return "true" if num else "false"
    if isinstance(num, int):
        return str(num)
    if isinstance(num, float):
        if num.is_integer():
            return str(int(num))
        return format % num
    raise ValueError(f"Unsupported type: {type(num)}")


def seq2str(seq: list[int | float | bool], sep = ",", format = "g") -> str:
    """Convert a sequence of numbers to a string, using the specified format for floats."""
    return sep.join(num2str(n, format) for n in seq)