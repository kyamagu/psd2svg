
import logging
import tempfile
import contextlib
import shutil

logger = logging.getLogger(__file__)


@contextlib.contextmanager
def temporary_directory(*args, **kwargs):
    """For Python 2.x compatibility."""
    d = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        shutil.rmtree(d)
