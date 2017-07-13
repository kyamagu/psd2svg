# -*- coding: utf-8 -*-
from contextlib import contextmanager
from logging import getLogger
import os
from tempfile import TemporaryFile
import mimetypes
from future.standard_library import install_aliases

install_aliases()

from urllib.parse import urlparse, urljoin
from urllib.request import urlopen, Request
from urllib.error import HTTPError


logger = getLogger(__name__)


def get_storage(dirname, **kwargs):
    result = urlparse(dirname)
    if not result.scheme:
        return FileSystemStorage(dirname, **kwargs)
    elif result.scheme == 's3':
        return S3Storage(result.netloc, result.path, **kwargs)
    else:
        return UrlStorage(dirname, **kwargs)


def _get_mime(filename):
    filetype, encoding = mimetypes.guess_type(filename)
    return filetype


class _BaseStorage(object):
    def open(self, key):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def exists(self, key):
        raise NotImplementedError

    def put(self, key, value):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def list(self):
        raise NotImplementedError

    def url(self, path=''):
        raise NotImplementedError


class FileSystemStorage(_BaseStorage):
    def __init__(self, path):
        self.basedir = path
        if not self.basedir:
            self.basedir = '.'

    def _ensure_dir(self, dirname):
        if not os.path.exists(dirname):
            logger.debug('Creating {}'.format(dirname))
            os.makedirs(dirname)

    @contextmanager
    def open(self, filename, mode='rb'):
        path = os.path.join(self.basedir, filename)
        if mode.startswith('w'):
            self._ensure_dir(os.path.dirname(path))
        with open(path, mode) as f:
            yield f

    def get(self, filename, mode='rb'):
        with self.open(filename, mode=mode) as f:
            return f.read()

    def exists(self, filename):
        return os.path.exists(os.path.join(self.basedir, filename))

    def put(self, filename, value, mode='wb'):
        with self.open(filename, mode=mode) as f:
            f.write(value)

    def delete(self, filename, **kwargs):
        os.remove(os.path.join(self.basedir, filename))

    def list(self):
        for path in os.listdir(self.basedir):
            yield path

    def url(self, path=''):
        return os.path.abspath(os.path.join(self.basedir, path))


class S3Storage(_BaseStorage):
    def __init__(self, bucket, key_prefix='', **kwargs):
        import boto3
        self.bucket = boto3.resource('s3').Bucket(bucket)
        self.key_prefix = key_prefix.lstrip('/')

        self.options = dict(ACL='public-read')
        self.options.update(kwargs)

    @contextmanager
    def open(self, key, mode='rb', **kwargs):
        key = os.path.join(self.key_prefix, key)
        if mode.startswith('r'):
            with TemporaryFile() as f:
                self.bucket.download_fileobj(key, f, **kwargs)
                f.seek(0)
                yield f
        elif mode.startswith('w'):
            with TemporaryFile() as f:
                yield f
                f.seek(0)
                self.bucket.upload_fileobj(f, key, **kwargs)
        else:
            raise ValueError('Unsupported mode {}'.format(mode))

    def get(self, key, **kwargs):
        with self.open(key, **kwargs) as f:
            return f.read()

    def exists(self, key):
        import botocore
        key = os.path.join(self.key_prefix, key)
        exists = True
        try:
            self.bucket.Object(key).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                exists = False
            else:
                raise
        return exists

    def put(self, key, value, **kwargs):
        key = os.path.join(self.key_prefix, key)
        options = dict(self.options)
        options.update(kwargs)
        self.bucket.Object(key).put(
            Body=value, ContentType=_get_mime(key),
            ContentDisposition='inline; filename="{}"'.format(
                os.path.basename(key)),
            **options)

    def delete(self, key, **kwargs):
        key = os.path.join(self.key_prefix, key)
        self.bucket.Object(key).delete(**kwargs)

    def list(self):
        for obj in self.bucket.objects.filter(Prefix=self.key_prefix):
            yield obj.key

    def url(self, path=''):
        return ('s3://' + self.bucket.name + '/' +
                os.path.normpath(os.path.join(self.key_prefix, path)))


class UrlStorage(_BaseStorage):
    def __init__(self, base_url, **kwargs):
        self.base_url = base_url

    @contextmanager
    def open(self, path, **kwargs):
        url = os.path.join(self.base_url, path)
        with TemporaryFile() as f:
            with urlopen(url, **kwargs) as response:
                f.write(response.read())
            f.seek(0)
            yield f

    def get(self, path, **kwargs):
        with self.open(path, **kwargs) as f:
            return f.read()

    def exists(self, path):
        url = os.path.join(self.base_url, path)
        request = Request(url, method='HEAD')
        exists = True
        try:
            urlopen(request)
        except HTTPError:
            exists = False
        return exists

    def url(self, path=''):
        return urljoin(self.base_url, path)
