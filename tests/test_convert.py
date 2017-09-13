import os
import pytest
from glob import glob
from psd2svg import psd2svg

FIXTURES = [
    p for p in glob(
        os.path.join(os.path.dirname(__file__), 'fixtures', '*.psd'))
    ]

@pytest.mark.parametrize('psd_file', FIXTURES)
def test_convert(tmpdir, psd_file):
    psd2svg(psd_file, tmpdir.dirname)
