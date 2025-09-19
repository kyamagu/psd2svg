import logging
import os

import psd_tools
import pytest

from psd2svg import Converter
from psd2svg.eval import check_quality

from .conftest import ALL, TYPES, FILLS, get_fixture


@pytest.mark.parametrize("psd_file", ALL)
def test_convert(tmpdir, psd_file: str) -> None:
    """Test converting PSD files to SVG."""

    input_path = get_fixture(psd_file)
    output_path = tmpdir.dirname + "/output.svg"
    images_path = tmpdir.dirname + "/images"
    Converter.convert(input_path, output_path, images_path)
    assert os.path.exists(output_path)


@pytest.mark.parametrize("psd_file", TYPES + FILLS)
def test_quality(psd_file: str) -> None:
    """Test conversion quality in the raster format."""

    input_path = get_fixture(psd_file)

    # Convert PSD to SVG.
    psdimage = psd_tools.PSDImage.open(input_path)
    converter = Converter(psdimage)
    converter.build()
    converter.embed_images()
    svg = converter.export()

    # Check quality.
    score = check_quality(psdimage, svg, "MSE")
    logging.info(f"MSE for {psd_file}: {score}")
    assert score < 0.05, f"MSE is too high: {score}"
