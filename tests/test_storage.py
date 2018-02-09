from __future__ import absolute_import, unicode_literals

import pytest
from psd2svg.storage import get_storage


@pytest.mark.parametrize("url, key", [
    ("https://github.com/kyamagu/", "psd2svg")
])
def test_url_read(url, key):
    storage = get_storage(url)
    assert storage.exists(key)
    assert storage.get(key)
    with storage.open(key) as f:
        assert f.read()


@pytest.mark.parametrize("key, value", [
    ("foo", b"bar"),
])
def test_file_readwrite(tmpdir, key, value):
    storage = get_storage(tmpdir.dirname)
    storage.put(key, value)
    assert storage.exists(key)
    assert storage.get(key) == value
    with storage.open(key) as f:
        assert f.read() == value
    storage.delete(key)
    assert not storage.exists(key)
