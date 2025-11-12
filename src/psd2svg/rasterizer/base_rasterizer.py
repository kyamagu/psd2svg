import logging
import tempfile
from abc import ABC, abstractmethod
from typing import Union

from PIL import Image

logger = logging.getLogger(__name__)


class BaseRasterizer(ABC):
    """Base class for SVG rasterizer implementations.

    This abstract base class defines the interface for converting SVG documents
    to raster images (PIL Image objects). Subclasses must implement the
    `from_file` method to provide the actual rasterization logic.
    """

    def from_string(self, svg_content: Union[str, bytes]) -> Image.Image:
        """Rasterize SVG content from a string or bytes to a PIL Image.

        This is a convenience method that writes the SVG content to a temporary
        file and calls `from_file`. Subclasses may override this for more
        efficient implementations.

        Args:
            svg_content: SVG content as string or bytes.

        Returns:
            PIL Image object containing the rasterized SVG.
        """
        with tempfile.NamedTemporaryFile(suffix=".svg", mode="wb", delete=False) as f:
            content_bytes = (
                svg_content
                if isinstance(svg_content, bytes)
                else svg_content.encode("utf-8")
            )
            f.write(content_bytes)
            f.flush()
            return self.from_file(f.name)

    @abstractmethod
    def from_file(self, filepath: str) -> Image.Image:
        """Rasterize an SVG file to a PIL Image.

        This is the primary method that subclasses must implement to provide
        the actual rasterization logic.

        Args:
            filepath: Path to the SVG file to rasterize.

        Returns:
            PIL Image object containing the rasterized SVG.
        """
        raise NotImplementedError

    def _composite_background(self, image: Image.Image) -> Image.Image:
        """Composite image onto a transparent background to normalize alpha.

        This utility method ensures consistent handling of transparent pixels
        by compositing the image onto a fully transparent RGBA background.
        This prevents artifacts and ensures proper alpha channel handling.

        Args:
            image: Input PIL Image, typically with RGBA mode.

        Returns:
            PIL Image with normalized alpha channel.
        """
        background = Image.new("RGBA", size=image.size, color=(255, 255, 255, 0))
        background.alpha_composite(image)
        return background
