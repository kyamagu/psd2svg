import os
from glob import glob

FIXTURES = [
    p for p in glob(
        os.path.join(os.path.dirname(__file__), 'fixtures', '*.psd'))
    ]