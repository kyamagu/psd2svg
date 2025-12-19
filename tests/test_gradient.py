from typing import Any

import pytest
from psd_tools.psd import descriptor
from psd_tools.terminology import Key, Klass, Unit

from psd2svg.core.gradient import GradientInterpolation


@pytest.fixture
def gradient_descriptor() -> Any:
    gradient = descriptor.Descriptor(classID=Klass.Gradient)
    # Set color stops.
    color1 = descriptor.Descriptor(classID=Klass.ColorStop)
    color1[Key.Color] = descriptor.Descriptor(classID=Klass.RGBColor)
    color1[Key.Color][Key.Red] = descriptor.Integer(255)
    color1[Key.Color][Key.Green] = descriptor.Integer(0)
    color1[Key.Color][Key.Blue] = descriptor.Integer(0)
    color1[Key.Location] = descriptor.Integer(0)
    color1[Key.Midpoint] = descriptor.Integer(50)
    color2 = descriptor.Descriptor(classID=Klass.ColorStop)
    color2[Key.Color] = descriptor.Descriptor(classID=Klass.RGBColor)
    color2[Key.Color][Key.Red] = descriptor.Integer(0)
    color2[Key.Color][Key.Green] = descriptor.Integer(0)
    color2[Key.Color][Key.Blue] = descriptor.Integer(255)
    color2[Key.Location] = descriptor.Integer(4096)
    color2[Key.Midpoint] = descriptor.Integer(50)
    gradient[Key.Colors] = descriptor.List([color1, color2])  # type: ignore[list-item]
    # Set opacity stops.
    opacity1 = descriptor.Descriptor(classID=Klass.TransparencyStop)
    opacity1[Key.Opacity] = descriptor.UnitFloat(unit=Unit.Percent, value=100)
    opacity1[Key.Location] = descriptor.Integer(0)
    opacity1[Key.Midpoint] = descriptor.Integer(50)
    opacity2 = descriptor.Descriptor(classID=Klass.TransparencyStop)
    opacity2[Key.Opacity] = descriptor.UnitFloat(unit=Unit.Percent, value=0)
    opacity2[Key.Location] = descriptor.Integer(4096)
    opacity2[Key.Midpoint] = descriptor.Integer(50)
    gradient[Key.Transparency] = descriptor.List([opacity1, opacity2])  # type: ignore[list-item]
    return gradient


def test_color_stops(gradient_descriptor: Any) -> None:
    interp = GradientInterpolation(gradient_descriptor)
    assert interp.color_stops[0][0] == 0.0
    assert interp.color_stops[-1][0] == 1.0
    assert len(interp.color_stops) == 2
    color1 = interp.get_color(0.0)
    assert isinstance(color1, descriptor.Descriptor)
    assert color1[Key.Red] == 255
    assert color1[Key.Green] == 0
    assert color1[Key.Blue] == 0
    color2 = interp.get_color(1.0)
    assert isinstance(color2, descriptor.Descriptor)
    assert color2[Key.Red] == 0
    assert color2[Key.Green] == 0
    assert color2[Key.Blue] == 255
    color3 = interp.get_color(0.5)
    assert isinstance(color3, descriptor.Descriptor)
    assert color3[Key.Red] == 127.5
    assert color3[Key.Green] == 0
    assert color3[Key.Blue] == 127.5


def test_opacity_stops(gradient_descriptor: Any) -> None:
    interp = GradientInterpolation(gradient_descriptor)
    assert interp.get_opacity(0.0) == 1.0
    assert interp.get_opacity(0.25) == 0.75
    assert interp.get_opacity(1.0) == 0.0


def test_iterator(gradient_descriptor: Any) -> None:
    interp = GradientInterpolation(gradient_descriptor)
    stops = list(interp)
    assert len(stops) == 2
    assert stops[0][0] == 0.0
    assert stops[0][2] == 1.0
    assert stops[1][0] == 1.0
    assert stops[1][2] == 0.0


def test_duplicate_color_stops() -> None:
    """Test that duplicate color stops don't cause division by zero.

    Duplicate stops at the same location.
    """
    gradient = descriptor.Descriptor(classID=Klass.Gradient)
    # Create two color stops at the same location (0.5)
    color1 = descriptor.Descriptor(classID=Klass.ColorStop)
    color1[Key.Color] = descriptor.Descriptor(classID=Klass.RGBColor)
    color1[Key.Color][Key.Red] = descriptor.Integer(255)
    color1[Key.Color][Key.Green] = descriptor.Integer(0)
    color1[Key.Color][Key.Blue] = descriptor.Integer(0)
    color1[Key.Location] = descriptor.Integer(2048)  # 0.5 * 4096
    color2 = descriptor.Descriptor(classID=Klass.ColorStop)
    color2[Key.Color] = descriptor.Descriptor(classID=Klass.RGBColor)
    color2[Key.Color][Key.Red] = descriptor.Integer(0)
    color2[Key.Color][Key.Green] = descriptor.Integer(255)
    color2[Key.Color][Key.Blue] = descriptor.Integer(0)
    color2[Key.Location] = descriptor.Integer(2048)  # Same location: 0.5 * 4096
    gradient[Key.Colors] = descriptor.List([color1, color2])  # type: ignore[list-item]
    # Set opacity stops (valid ones)
    opacity1 = descriptor.Descriptor(classID=Klass.TransparencyStop)
    opacity1[Key.Opacity] = descriptor.UnitFloat(unit=Unit.Percent, value=100)
    opacity1[Key.Location] = descriptor.Integer(0)
    opacity2 = descriptor.Descriptor(classID=Klass.TransparencyStop)
    opacity2[Key.Opacity] = descriptor.UnitFloat(unit=Unit.Percent, value=100)
    opacity2[Key.Location] = descriptor.Integer(4096)
    gradient[Key.Transparency] = descriptor.List([opacity1, opacity2])  # type: ignore[list-item]

    interp = GradientInterpolation(gradient)
    # Should not raise ZeroDivisionError and should return the first color
    color = interp.get_color(0.5)
    assert isinstance(color, descriptor.Descriptor)
    assert color[Key.Red] == 255
    assert color[Key.Green] == 0
    assert color[Key.Blue] == 0


def test_duplicate_opacity_stops() -> None:
    """Test that duplicate opacity stops don't cause division by zero.

    Duplicate stops at the same location.
    """
    gradient = descriptor.Descriptor(classID=Klass.Gradient)
    # Set color stops (valid ones)
    color1 = descriptor.Descriptor(classID=Klass.ColorStop)
    color1[Key.Color] = descriptor.Descriptor(classID=Klass.RGBColor)
    color1[Key.Color][Key.Red] = descriptor.Integer(255)
    color1[Key.Color][Key.Green] = descriptor.Integer(0)
    color1[Key.Color][Key.Blue] = descriptor.Integer(0)
    color1[Key.Location] = descriptor.Integer(0)
    color2 = descriptor.Descriptor(classID=Klass.ColorStop)
    color2[Key.Color] = descriptor.Descriptor(classID=Klass.RGBColor)
    color2[Key.Color][Key.Red] = descriptor.Integer(0)
    color2[Key.Color][Key.Green] = descriptor.Integer(0)
    color2[Key.Color][Key.Blue] = descriptor.Integer(255)
    color2[Key.Location] = descriptor.Integer(4096)
    gradient[Key.Colors] = descriptor.List([color1, color2])  # type: ignore[list-item]
    # Create two opacity stops at the same location (0.5)
    opacity1 = descriptor.Descriptor(classID=Klass.TransparencyStop)
    opacity1[Key.Opacity] = descriptor.UnitFloat(unit=Unit.Percent, value=100)
    opacity1[Key.Location] = descriptor.Integer(2048)  # 0.5 * 4096
    opacity2 = descriptor.Descriptor(classID=Klass.TransparencyStop)
    opacity2[Key.Opacity] = descriptor.UnitFloat(unit=Unit.Percent, value=50)
    opacity2[Key.Location] = descriptor.Integer(2048)  # Same location: 0.5 * 4096
    gradient[Key.Transparency] = descriptor.List([opacity1, opacity2])  # type: ignore[list-item]

    interp = GradientInterpolation(gradient)
    # Should not raise ZeroDivisionError and should return the first opacity
    opacity = interp.get_opacity(0.5)
    assert opacity == 1.0  # 100% / 100.0
