import base64
import hashlib
import io
import os
import xml.dom.minidom as minidom
from logging import getLogger
from typing import IO, Optional, Union

from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import Layer

from psd2svg.deprecated.base import ConverterProtocol

logger = getLogger(__name__)


class PSDReader:
    def _set_input(self: ConverterProtocol, input_data: Union[str, IO, PSDImage, Layer]) -> None:
        if hasattr(input_data, "read"):
            self._load_stream(input_data)
        elif hasattr(input_data, "topil"):
            self._load_psd(input_data)
        else:
            self._load_file(input_data)

    def _load_file(self: ConverterProtocol, filepath: str) -> None:
        logger.debug(f"Opening {filepath}")
        with open(filepath, "rb") as f:
            self._load_stream(f)
        self._input = filepath

    def _load_stream(self: ConverterProtocol, stream: IO) -> None:
        self._input = None
        self._psd = PSDImage.open(stream)
        self._layer = self._psd

    def _load_psd(self: ConverterProtocol, psd: Union[PSDImage, Layer]) -> None:
        self._input = None
        self._layer = psd
        while psd.parent is not None:
            psd = psd.parent
        self._psd = psd


class SVGWriter:
    def _set_output(self: ConverterProtocol, output_data: Optional[Union[str, IO]]) -> None:
        # IO object.
        self._resource_dir = None
        if not output_data:
            self._output = None
            if self.resource_path is not None:
                self._resource_dir = self.resource_path
            self._output_file = None
            return
        if hasattr(output_data, "write"):
            self._output = output_data
            if self.resource_path is not None:
                self._resource_dir = self.resource_path
            self._output_file = None
            return

        # Else save to a file.
        if not output_data.endswith("/") and os.path.isdir(output_data):
            output_data += "/"
        self._output_dir = os.path.dirname(output_data)
        if self.resource_path is not None:
            if os.path.isabs(self.resource_path):
                self._resource_dir = self.resource_path
            else:
                self._resource_dir = os.path.join(self._output_dir, self.resource_path)
        self._output_file = os.path.basename(output_data)
        if not self._output_file:
            if self._input:
                basename = os.path.splitext(os.path.basename(self._input))[0]
                self._output_file = basename + ".svg"
            else:
                raise ValueError(f"Invalid output: {output_data}")

    def _save_svg(self) -> Union[str, IO]:
        # Write to the output.
        pretty_string = self._get_svg()
        if self._output_file:
            output_path = os.path.join(self._output_dir, self._output_file)
            logger.info(f"Saving {output_path}")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(pretty_string)
            return output_path
        elif self._output:
            self._output.write(pretty_string)
            return self._output
        else:
            return pretty_string

    def _get_svg(self) -> str:
        with io.StringIO() as f:
            # svgwrite's pretty option is not compatible with Python 2.7
            # unicode. Here we manually encode utf-8.
            self.dwg.write(f, pretty=False)
            xml_string = f.getvalue().encode("utf-8")

        xml_tree = minidom.parseString(xml_string)
        return xml_tree.toprettyxml(indent="  ")

    def _get_image_href(
        self: ConverterProtocol, image: Image.Image, fmt: str = "png", icc_profile: Optional[bytes] = None
    ) -> str:
        if image.mode == "CMYK":
            image = image.convert("RGB")
        with io.BytesIO() as output:
            image.save(output, format=fmt, icc_profile=icc_profile)
            encoded_image = output.getvalue()
        if self._resource_dir is not None:
            checksum = hashlib.md5(encoded_image).hexdigest()
            filename = checksum + "." + fmt
            # Create resource directory if it doesn't exist
            os.makedirs(self._resource_dir, exist_ok=True)
            resource_path = os.path.join(self._resource_dir, filename)
            logger.info(f"Saving {resource_path}")
            with open(resource_path, "wb") as f:
                f.write(encoded_image)
            href = os.path.join(self.resource_path, filename)
        else:
            href = f"data:image/{fmt};base64," + base64.b64encode(encoded_image).decode(
                "utf-8"
            )
        return href
