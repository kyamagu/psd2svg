from psd2svg.storage import get_storage


def _read_functions(storage, key):
    assert storage.exists(key)
    assert storage.get(key)
    with storage.open(key) as f:
        assert f.read()


def _readwrite_functions(storage, key, value):
    storage.put(key, value)
    assert storage.exists(key)
    assert storage.get(key) == value
    with storage.open(key) as f:
        assert f.read() == value
    storage.delete(key)
    assert not storage.exists(key)


def test_filestorage(tmpdir):
    storage = get_storage(tmpdir.dirname)
    _readwrite_functions(storage, 'foo', b'bar')


# def test_s3storage():
#     storage = get_storage('s3://bucket/path/to/target')
#     _readwrite_functions(storage, 'foo', b'bar')


def test_urlstorage():
    storage = get_storage('https://github.com/kyamagu/')
    _read_functions(storage, 'psd2svg')
