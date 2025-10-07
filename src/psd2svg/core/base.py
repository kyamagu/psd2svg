import contextlib
import xml.etree.ElementTree as ET
from typing import Iterator, Protocol

from PIL import Image
from psd_tools import PSDImage
from psd_tools.api import layers


class ConverterProtocol(Protocol):
    """Converter state protocol."""

    psd: PSDImage
    svg: ET.Element
    current: ET.Element
    images: list[Image.Image]

    def add_layer(self, layer: layers.Layer) -> ET.Element | None: ...
    def add_group(self, group: layers.Group) -> ET.Element | None: ...
    def add_pixel(self, layer: layers.Layer) -> ET.Element | None: ...
    def add_shape(self, layer: layers.ShapeLayer) -> ET.Element | None: ...
    def add_adjustment(self, layer: layers.AdjustmentLayer) -> ET.Element | None: ...
    def add_type(self, layer: layers.TypeLayer) -> ET.Element | None: ...
    def add_fill(self, layer: layers.FillLayer) -> ET.Element | None: ...

    def set_layer_attributes(self, layer: layers.Layer, node: ET.Element) -> None: ...
    def set_isolation(self, layer: layers.Layer, node: ET.Element) -> None: ...
    def set_mask(self, layer: layers.Layer, node: ET.Element) -> None: ...
    def set_opacity(self, opacity: float, node: ET.Element) -> None: ...
    def set_blend_mode(self, psd_mode: bytes | str, node: ET.Element) -> None: ...

    @contextlib.contextmanager
    def add_clipping_target(
        self, layer: layers.Layer | layers.Group
    ) -> Iterator[None]: ...

    def apply_drop_shadow_effect(
        self,
        layer: layers.Layer,
        target: ET.Element,
        insert_before_target: bool = False,
    ) -> None: ...
    def apply_outer_glow_effect(
        self,
        layer: layers.Layer,
        target: ET.Element,
        insert_before_target: bool = False,
    ) -> None: ...
    def apply_color_overlay_effect(
        self, layer: layers.Layer, target: ET.Element
    ) -> None: ...
    def apply_stroke_effect(self, layer: layers.Layer, target: ET.Element) -> None: ...

    def auto_id(self, prefix: str = "") -> str: ...

    @contextlib.contextmanager
    def set_current(self, node: ET.Element) -> Iterator[None]:
        """Set the current node for the converter."""
        previous = self.current
        self.current = node
        try:
            yield
        finally:
            self.current = previous