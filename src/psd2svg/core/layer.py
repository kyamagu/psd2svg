import logging
from xml.etree import ElementTree as ET

from psd_tools.api import layers

from psd2svg.core.base import ConverterProtocol
from psd2svg.core.svg_utils import create_node

logger = logging.getLogger(__name__)


class LayerConverter(ConverterProtocol):
    """Main layer converter mixin."""

    def add_layer(self, layer: layers.Layer) -> ET.Element | None:
        """Add a layer to the svg document."""
        if not layer.is_visible():
            # TODO: Option to include hidden layers.
            logger.debug(f"Layer '{layer.name}' is not visible.")
            return None

        # Simple registry-based dispatch.
        registry = {
            # TODO: Support more layer types here.
            layers.Group: self.add_group,
            # layers.AdjustmentLayer: self.add_adjustment,
            # layers.ShapeLayer: self.add_shape,
            # layers.TypeLayer: self.add_type,
            layers.PixelLayer: self.add_pixel,
        }
        # Default handler is a plain pixel layer.
        handler = registry.get(type(layer), self.add_pixel)
        return handler(layer)

    def add_group(self, group: layers.Group) -> ET.Element | None:
        """Add a group layer to the svg document."""
        previous = self.current  # type: ignore
        group_node = create_node("g", parent=previous, class_="group", title=group.name)
        self.current = group_node
        for child in group:
            self.add_layer(child)
        self.current = previous
        return group_node

    def add_pixel(self, layer: layers.Layer) -> ET.Element | None:
        """Add a general pixel-based layer to the svg document."""
        if not layer.has_pixels():
            logger.debug(f"Layer '{layer.name}' has no pixels.")
            return None
        
        self.images.append(layer.composite())
        return create_node(
            "image",
            parent=self.current,
            x=layer.left,
            y=layer.top,
            width=layer.width,
            height=layer.height,
            class_=layer.kind,
            title=layer.name,
        )
