import contextlib
import logging
import shutil
import tempfile
from collections.abc import Generator
from typing import Any

logger = logging.getLogger(__file__)


@contextlib.contextmanager
def temporary_directory(*args: Any, **kwargs: Any) -> Generator[str, None, None]:
    """For Python 2.x compatibility."""
    d = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        shutil.rmtree(d)
