import logging
from typing import Iterator

from psd_tools.psd.descriptor import Descriptor
from psd_tools.terminology import Key, Klass

logger = logging.getLogger(__name__)


class GradientInterpolation:
    """Helper to handle gradient interpolation from a PSD Descriptor.

    Example:

        interpolator = GradientInterpolation(descriptor)
        for location, color, opacity in interpolator:
            # location: float (0.0-1.0)
            # color: Descriptor (RGBColor)
            # opacity: float (0.0-1.0)

    Args:
        descriptor (Descriptor): PSD Gradient descriptor.
    """

    def __init__(self, descriptor: Descriptor):
        if descriptor.classID != Klass.Gradient:
            raise ValueError("Descriptor is not a Gradient")
        self.descriptor = descriptor
        self._build_color_stops()
        self._build_opacity_stops()

    def _build_color_stops(self):
        """Build color stops from the gradient descriptor."""
        if len(self.descriptor[Key.Colors]) <= 0:
            raise ValueError("No color stops found in gradient descriptor")
        # Color is in RGBC or other color descriptor format.
        # Normalize location from 0-4096 to 0.0-1.0.
        color_stops: list[tuple[float, Descriptor]] = sorted(
            [  # type: ignore
                (int(stop[Key.Location]) / 4096.0, stop[Key.Color])
                for stop in self.descriptor[Key.Colors]
            ],
            key=lambda x: x[0],
        )
        if color_stops[0][0] != 0.0:
            color_stops.insert(0, (0.0, color_stops[0][1]))
        if color_stops[-1][0] != 1.0:
            color_stops.append((1.0, color_stops[-1][1]))
        self.color_stops = color_stops

    def _build_opacity_stops(self):
        """Build opacity stops from the gradient descriptor."""
        if len(self.descriptor[Key.Transparency]) <= 0:
            raise ValueError("No transparency stops found in gradient descriptor")
        # Normalize location from 0-4096 to 0.0-1.0.
        # Opacity is in percentage (0-100).
        opacity_stops = sorted(
            [
                (int(stop[Key.Location]) / 4096.0, float(stop[Key.Opacity]))
                for stop in self.descriptor[Key.Transparency]
            ],
            key=lambda x: x[0],
        )
        if opacity_stops[0][0] != 0.0:
            opacity_stops.insert(0, (0.0, opacity_stops[0][1]))
        if opacity_stops[-1][0] != 1.0:
            opacity_stops.append((1.0, opacity_stops[-1][1]))
        self.opacity_stops = opacity_stops

    def get_color(self, location: float) -> Descriptor:
        """Compute the interpolated color at a given location.

        Args:
            location: Normalized location (0.0-1.0).

        Returns:
            Descriptor: Interpolated color descriptor.
        """
        if location < 0.0 or location > 1.0:
            raise ValueError("Location must be between 0.0 and 1.0")
        for i in range(1, len(self.color_stops)):
            if location <= self.color_stops[i][0]:
                loc0, color0 = self.color_stops[i - 1]
                loc1, color1 = self.color_stops[i]
                t = (location - loc0) / (loc1 - loc0)
                # Simple linear interpolation for color channels.
                # TODO: Midpoint support.
                desc = Descriptor(classID=color0.classID)
                for key in color0.keys():
                    desc[key] = float(color0[key]) + t * (
                        float(color1[key]) - float(color0[key])
                    )
                return desc
        return self.color_stops[-1][1]

    def get_opacity(self, location: float) -> float:
        """Compute the interpolated opacity at a given location.

        Args:
            location: Normalized location (0.0-1.0).

        Returns:
            float: Normalized opacity value (0.0-1.0).
        """
        if location < 0.0 or location > 1.0:
            raise ValueError("Location must be between 0.0 and 1.0")
        for i in range(1, len(self.opacity_stops)):
            if location <= self.opacity_stops[i][0]:
                loc0, op0 = self.opacity_stops[i - 1]
                loc1, op1 = self.opacity_stops[i]
                t = (location - loc0) / (loc1 - loc0)
                # TODO: Midpoint support.
                interpolated_opacity = op0 + t * (op1 - op0)
                return interpolated_opacity / 100.0
        return self.opacity_stops[-1][1] / 100.0

    def __iter__(self) -> Iterator[tuple[float, Descriptor, float]]:
        """Get all stops with color and opacity.

        Yields:
            tuple: (location, color, opacity) where location is 0.0-1.0.
        """
        locations = set(loc for loc, _ in self.color_stops) | set(
            loc for loc, _ in self.opacity_stops
        )
        for location in sorted(list(locations)):
            color = self.get_color(location)
            opacity = self.get_opacity(location)
            yield (location, color, opacity)
