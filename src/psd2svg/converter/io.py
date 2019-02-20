# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import base64
import hashlib
import io
from logging import getLogger
import os
from psd_tools import PSDImage
from psd_tools.api.layers import Layer
from psd2svg.storage import get_storage
import xml.dom.minidom as minidom


logger = getLogger(__name__)


class PSDReader(object):

    def _set_input(self, input_data):
        if hasattr(input_data, 'read'):
            self._load_stream(input_data)
        elif hasattr(input_data, 'topil'):
            self._load_psd(input_data)
        else:
            self._load_storage(input_data)

    def _load_storage(self, url):
        storage = get_storage(os.path.dirname(url))
        filename = os.path.basename(url)
        logger.debug('Opening {}'.format(url))
        with storage.open(filename) as f:
            self._load_stream(f)
        self._input = url

    def _load_stream(self, stream):
        self._input = None
        self._psd = PSDImage.open(stream)
        self._layer = self._psd

    def _load_psd(self, psd):
        self._input = None
        self._layer = psd
        while psd.parent is not None:
            psd = psd.parent
        self._psd = psd


class SVGWriter(object):

    def _set_output(self, output_data):
        # IO object.
        self._resource = None
        if not output_data:
            self._output = None
            if self.resource_path is not None:
                self._resource = get_storage(self.resource_path)
            self._output_file = None
            return
        if hasattr(output_data, 'write'):
            self._output = output_data
            if self.resource_path is not None:
                self._resource = get_storage(self.resource_path)
            self._output_file = None
            return

        # Else save to a file.
        if not output_data.endswith('/') and os.path.isdir(output_data):
            output_data += '/'
        self._output = get_storage(os.path.dirname(output_data))
        if self.resource_path is not None:
            self._resource = get_storage(self._output.url(self.resource_path))
        self._output_file = os.path.basename(output_data)
        if not self._output_file:
            if self._input:
                basename = os.path.splitext(os.path.basename(self._input))[0]
                self._output_file = basename + '.svg'
            else:
                raise ValueError('Invalid output: {}'.format(output_data))

    def _save_svg(self):
        # Write to the output.
        pretty_string = self._get_svg()
        if self._output_file:
            url = self._output.url(self._output_file)
            logger.info('Saving {}'.format(url))
            self._output.put(self._output_file, pretty_string.encode('utf-8'))
            return url
        elif self._output:
            self._output.write(pretty_string)
            return self._output
        else:
            return pretty_string

    def _get_svg(self):
        with io.StringIO() as f:
            # svgwrite's pretty option is not compatible with Python 2.7
            # unicode. Here we manually encode utf-8.
            self._dwg.write(f, pretty=False)
            xml_string = f.getvalue().encode('utf-8')

        xml_tree = minidom.parseString(xml_string)
        return xml_tree.toprettyxml(indent='  ')

    def _get_image_href(self, image, fmt='png', icc_profile=None):
        with io.BytesIO() as output:
            image.save(output, format=fmt, icc_profile=icc_profile)
            encoded_image = output.getvalue()
        if self._resource is not None:
            checksum = hashlib.md5(encoded_image).hexdigest()
            filename = checksum + '.' + fmt
            # if not self._resource.exists(filename):
            logger.info('Saving {}'.format(self._resource.url(filename)))
            self._resource.put(filename, encoded_image)
            href = os.path.join(self.resource_path, filename)
        else:
            href = ('data:image/{};base64,'.format(fmt) +
                    base64.b64encode(encoded_image).decode('utf-8'))
        return href
