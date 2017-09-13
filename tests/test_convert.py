import os
import pytest
from glob import glob
from psd2svg import psd2svg


FIXTURES = [
    'layer-effects.psd',
    'patterns.psd'
]

EXTERNAL_FIXTURES = [
    p for p in glob('/Users/a14824/projects/psd-tools/tests/psd_files/*.psd')
    ]

@pytest.mark.parametrize('psd_file', FIXTURES)
def test_convert(tmpdir, psd_file):
    psd_path = os.path.join(os.path.dirname(__file__), 'fixtures', psd_file)
    psd2svg(psd_path, tmpdir.dirname)


@pytest.mark.parametrize('psd_path', EXTERNAL_FIXTURES)
def test_convert_external(tmpdir, psd_path):
    psd2svg(psd_path, tmpdir.dirname)
