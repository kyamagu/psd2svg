import base64
import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def encode_image(image: Image.Image, format: str = "WEBP") -> bytes:
    """Encode a PIL image to bytes in the specified format.

    For JPEG format, RGBA images are automatically converted to RGB with a white background.
    """
    # Convert RGBA to RGB for JPEG format (JPEG doesn't support alpha)
    if format.upper() == "JPEG" and image.mode == "RGBA":
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])  # Use alpha as mask
        image = rgb_image

    with io.BytesIO() as output:
        image.save(output, format=format.upper())
        return output.getvalue()


def encode_data_uri(image: Image.Image, format: str = "WEBP") -> str:
    """Encode a PIL image as a base64 data URI.

    For JPEG format, RGBA images are automatically converted to RGB with a white background.
    """
    image_bytes = encode_image(image, format)
    base64_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/{format.lower()};base64,{base64_data}"


def decode_image(data: bytes, mode: str | None = None) -> Image.Image:
    """Decode image data from bytes to a PIL image."""
    with io.BytesIO(data) as input:
        image = Image.open(input)
        image.load()
    if mode is not None:
        return image.convert(mode)
    return image


def decode_data_uri(data_uri: str, mode: str | None = None) -> Image.Image:
    """Decode a base64 data URI to a PIL image."""
    _, base64_data = data_uri.split(",", 1)
    data = base64.b64decode(base64_data)
    return decode_image(data, mode)
