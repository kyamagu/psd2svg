from __future__ import absolute_import, unicode_literals

from builtins import str
import os
import pytest
import io
from glob import glob
from psd_tools import PSDImage
from psd2svg import psd2svg

FIXTURES = [
    p for p in glob(
        os.path.join(os.path.dirname(__file__), 'fixtures', '*.psd'))
    ]

@pytest.mark.parametrize('psd_file', FIXTURES)
def test_convert(tmpdir, psd_file):
    psd2svg(psd_file, tmpdir.dirname)


@pytest.mark.parametrize('psd_file', FIXTURES[0:1])
def test_input_io(tmpdir, psd_file):
    with open(psd_file, "rb") as f:
        assert isinstance(psd2svg(f), str)


@pytest.mark.parametrize('psd_file', FIXTURES[0:1])
def test_input_psd(tmpdir, psd_file):
    psd = PSDImage.open(psd_file)
    psd2svg(psd)


@pytest.mark.parametrize('psd_file', FIXTURES[2:3])
def test_input_layer(tmpdir, psd_file):
    psd = PSDImage.open(psd_file)
    assert psd2svg(psd[0]).startswith("<")


@pytest.mark.parametrize('psd_file', FIXTURES[0:1])
def test_output_io(tmpdir, psd_file):
    with io.StringIO() as f:
        assert f == psd2svg(psd_file, f)
