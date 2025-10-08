import collections
import logging

logger = logging.getLogger(__name__)


class AutoCounter:
    """A simple auto-incrementing counter for generating unique IDs."""

    def __init__(self, delimiter: str = "_") -> None:
        self.names: collections.defaultdict[str, int] = collections.defaultdict(int)
        self.delimiter = delimiter

    def get_id(self, base: str) -> str:
        """Get a unique ID based on the base name."""
        self.names[base] += 1
        return (
            f"{base}{self.delimiter}{self.names[base]:g}"
            if self.names[base] > 1
            else base
        )
