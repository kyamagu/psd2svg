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
        assert isinstance(psd2svg(f), bytes)


@pytest.mark.parametrize('psd_file', FIXTURES[0:1])
def test_input_psd(tmpdir, psd_file):
    psd = PSDImage.load(psd_file)
    psd2svg(psd)


@pytest.mark.parametrize('psd_file', FIXTURES[0:1])
def test_input_layer(tmpdir, psd_file):
    psd = PSDImage.load(psd_file)
    assert psd2svg(psd.layers[2]).startswith(b"<")


@pytest.mark.parametrize('psd_file', FIXTURES[0:1])
def test_output_io(tmpdir, psd_file):
    with io.BytesIO() as f:
        assert f == psd2svg(psd_file, f)
