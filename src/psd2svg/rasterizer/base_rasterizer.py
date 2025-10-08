import logging
import tempfile
from typing import Any, Optional, Union

from PIL import Image

logger = logging.getLogger(__name__)


class BaseRasterizer:
    """Base class for rasterizer implementation."""

    def rasterize_from_string(
        self, input: Union[str, bytes], **kwargs: Any
    ) -> Image.Image:
        with tempfile.NamedTemporaryFile(suffix=".svg") as f:
            f.write(input if isinstance(input, bytes) else input.encode("utf-8"))
            f.flush()
            return self.rasterize(f.name, **kwargs)

    def rasterize(
        self, url: str, size: Optional[tuple[int, int]] = None, **kwargs: Any
    ) -> Image.Image:
        raise NotImplementedError

    def composite_background(self, image: Image.Image) -> Image.Image:
        background = Image.new("RGBA", size=image.size, color=(255, 255, 255, 0))
        background.alpha_composite(image)
        return background
