import os
import pytest
from psd2svg import psd2svg


FIXTURES = [
    'layer-effects.psd',
    'patterns.psd'
]

@pytest.mark.parametrize('psd_file', FIXTURES)
def test_convert(tmpdir, psd_file):
    psd_path = os.path.join(os.path.dirname(__file__), 'fixtures', psd_file)
    psd2svg(psd_path, tmpdir.dirname)
