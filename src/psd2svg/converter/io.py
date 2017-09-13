# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import base64
import hashlib
import io
from logging import getLogger
import os
import psd_tools
from psd2svg.storage import get_storage
import xml.dom.minidom as minidom


logger = getLogger(__name__)


class PSDReader(object):

    def _load(self, url):
        storage = get_storage(os.path.dirname(url))
        filename = os.path.basename(url)
        logger.info('Opening {}'.format(url))
        with storage.open(filename) as f:
            self._load_stream(f)
        self._input = url

    def _load_stream(self, stream):
        self._input = None
        self._psd = psd_tools.PSDImage.from_stream(stream)


class SVGWriter(object):

    def _set_output(self, output_url):
        if not output_url.endswith('/') and os.path.isdir(output_url):
            output_url += '/'
        self._output = get_storage(os.path.dirname(output_url))
        self._resource = get_storage(
            self._output.url(self.resource_prefix))

        self._output_file = os.path.basename(output_url)
        if not self._output_file:
            if self._input:
                basename = os.path.splitext(os.path.basename(self._input))[0]
                self._output_file = basename + '.svg'
            else:
                raise ValueError('Invalid output: {}'.format(output_url))

    def _save_svg(self):
        # Write to the output.
        url = self._output.url(self._output_file)
        logger.info('Saving {}'.format(url))
        with io.StringIO() as f:
            # svgwrite's pretty option is not compatible with Python 2.7
            # unicode. Here we manually encode utf-8.
            self._dwg.write(f, pretty=False)
            xml_string = f.getvalue().encode('utf-8')
            xml_tree = minidom.parseString(xml_string)
            pretty_string = xml_tree.toprettyxml(indent='  ').encode('utf-8')
            self._output.put(self._output_file, pretty_string)
        return url

    def _get_image_href(self, image, fmt='png', icc_profile=None):
        output = io.BytesIO()
        image.save(output, format=fmt, icc_profile=icc_profile)
        encoded_image = output.getvalue()
        output.close()
        checksum = hashlib.md5(encoded_image).hexdigest()
        if self.export_resource:
            filename = checksum + '.' + fmt
            if self.overwrite or not self._resource.exists(filename):
                logger.info('Saving {}'.format(
                    self._resource.url(filename)))
                self._resource.put(filename, encoded_image)
            href = os.path.join(self.resource_prefix, filename)
        else:
            href = ('data:image/{};base64,'.format(fmt) +
                    base64.b64encode(encoded_image).decode('utf-8'))
        return href
