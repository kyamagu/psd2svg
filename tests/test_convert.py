import pytest

from psd2svg import Converter

from .conftest import FIXTURES


@pytest.mark.parametrize('psd_file', FIXTURES)
def test_convert(tmpdir, psd_file: str) -> None:
    Converter.convert(psd_file, tmpdir.dirname + "/output.svg")