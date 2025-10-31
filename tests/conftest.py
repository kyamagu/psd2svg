import logging
import os

logger = logging.getLogger(__name__)


def get_fixture(name: str) -> str:
    """Get a fixture by name."""
    return os.path.join(os.path.dirname(__file__), "fixtures", name)
