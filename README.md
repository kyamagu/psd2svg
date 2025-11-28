# PSD2SVG

PSD to SVG converter based on [psd-tools](https://github.com/psd-tools/psd-tools).

[![PyPI Version](https://img.shields.io/pypi/v/psd2svg.svg)](https://pypi.python.org/pypi/psd2svg)
[![Documentation Status](https://readthedocs.org/projects/psd2svg/badge/?version=latest)](https://psd2svg.readthedocs.io/en/latest/?badge=latest)

## Install

Use `pip` to install:

```bash
pip install psd2svg
```

## Usage

The package comes with a command-line tool:

```bash
psd2svg input.psd output.svg
```

When the output path is a directory, or omitted, the tool infers the output name from the input:

```bash
psd2svg input.psd output/  # => output/input.svg
psd2svg input.psd          # => input.svg
```

When `--images-path` flag is specified, all png resources are exported to the path specified by `--images-path`:

```bash
psd2svg input.psd output.svg --images-path .
# => output.svg, xxx1.png, ...

psd2svg input.psd output/ --images-path .
# => output/input.svg, output/xxx1.png, ...

psd2svg input.psd output/ --images-path=resources/
# => output/input.svg, output/resources/xxx1.png, ...

psd2svg input.psd svg/ --images-path=../png/
# => svg/input.svg, png/xxx1.png, ...
```

## API

### Simple conversion

The package provides a simple `convert()` function for quick conversions:

```python
from psd2svg import convert

# Convert PSD to SVG with embedded images
convert('input.psd', 'output.svg')

# Convert PSD to SVG with external images
convert('input.psd', 'output.svg', image_prefix='images/img_')
# => output.svg, images/img_01.webp, images/img_02.webp, ...
```

### SVGDocument API

For more control, use the `SVGDocument` class:

```python
from psd_tools import PSDImage
from psd2svg import SVGDocument

# Create from PSDImage
psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)

# Save to file with embedded images
document.save("output.svg", embed_images=True)

# Save to file with external images
document.save("output.svg", image_prefix="images/img_", image_format="png")

# Get as string
svg_string = document.tostring(embed_images=True)
print(svg_string)

# Rasterize to PIL Image using resvg
image = document.rasterize()
image.save('output.png')

# Export and load back
exported = document.export()
document = SVGDocument.load(exported["svg"], exported["images"])
```

### Configuration Options

#### Title Elements

By default, each layer in the SVG includes a `<title>` element with the Photoshop layer name for accessibility and debugging. You can disable this to reduce file size:

```python
from psd2svg import SVGDocument, convert
from psd_tools import PSDImage

# Using SVGDocument
psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(
    psdimage,
    enable_title=False  # omit <title> elements
)

# Using convert()
convert('input.psd', 'output.svg', enable_title=False)
```

**Note:** Text layers never include title elements (even with `enable_title=True`) since the layer name is typically the same as the visible text content.

#### Text Letter Spacing Adjustment

Photoshop and SVG renderers may have slightly different default letter spacing. You can adjust this with the `text_letter_spacing_offset` parameter:

```python
from psd2svg import SVGDocument, convert
from psd_tools import PSDImage

# Using SVGDocument
psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(
    psdimage,
    text_letter_spacing_offset=-0.015  # tighten spacing by 0.015 pixels
)

# Using convert()
convert('input.psd', 'output.svg', text_letter_spacing_offset=-0.015)
```

The offset (in pixels) is added to all letter-spacing values. Typical values range from -0.02 to 0.02. Experiment to find the best value for your fonts and target renderers.

### Rasterization

The package includes rasterizer support using resvg to convert SVG to PIL Image:

```python
from psd2svg import SVGDocument

document = SVGDocument.from_psd(psdimage)

# Built-in rasterize method (uses resvg)
image = document.rasterize()
image.save('output.png')

# Rasterize with custom DPI
image = document.rasterize(dpi=300)
image.save('output_high_res.png')

# Or use rasterizer directly
from psd2svg.rasterizer import ResvgRasterizer

rasterizer = ResvgRasterizer(dpi=96)
svg_string = document.tostring(embed_images=True)
image = rasterizer.rasterize_from_string(svg_string)
image.save('output.png')
```

The `resvg-py` package is included as a dependency, providing fast and accurate SVG rendering with no external dependencies.

## Documentation

Comprehensive documentation is available and built with Sphinx.

### Building Documentation

To build the HTML documentation locally:

```bash
# Install documentation dependencies
uv sync --group docs

# Build the documentation
uv run sphinx-build -b html docs docs/_build/html

# Open the documentation in your browser
open docs/_build/html/index.html  # macOS
xdg-open docs/_build/html/index.html  # Linux
start docs/_build/html/index.html  # Windows
```

The documentation includes:

- **Getting Started** - Installation and quick start guide
- **User Guide** - Comprehensive usage documentation
- **API Reference** - Complete API documentation with examples
- **Rasterizers Guide** - Details on all rasterizer backends
- **Development Guide** - Contributing and development setup
- **Limitations** - Known limitations and workarounds

### Online Documentation

Full documentation is available at [psd2svg.readthedocs.io](https://psd2svg.readthedocs.io/)

## Test

Run tests with pytest:

```bash
pytest
```

## Notes

- SVG 1.1 does not cover all the blending modes in Photoshop (e.g., `linear-dodge`)
- Filter effects are approximation. Some effects are not implemented.
- Most of adjustments layers are not implemented.
- Smart object filters are not implemented.
- Browser support: SVG rendering quality greatly differs depending on the browser. Chrome tends to be the best quality.
- APIs of this tool is NOT thread-safe.

### Experimental: Text Layer Conversion

Text layer conversion to SVG `<text>` elements is **experimental** and enabled by default. Text layers are converted to native SVG text with proper styling when possible.

**Supported text features:**

- Font family, size, weight (bold), and style (italic)
- Faux bold and faux italic
- Text decoration (underline, strikethrough)
- Text transformation (all-caps, small-caps)
- Superscript and subscript
- Baseline shift, letter spacing (tracking), and line height (leading)
- Horizontal and vertical text scaling
- Text alignment and vertical writing modes

**Known limitations:**

- Requires fonts to be installed on your system
- Only solid colors supported (no gradients or patterns for text)
- Text wrapping in bounding boxes not fully supported
- Kerning and ligatures not supported
- Text scaling may not work in older SVG 1.1 renderers

To disable and fall back to rasterization:

```python
from psd2svg.core.converter import Converter

converter = Converter(psdimage, enable_text=False)
```

See the documentation for complete details on text layer support and limitations.
