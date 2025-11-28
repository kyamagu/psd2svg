# PSD2SVG

PSD to SVG converter based on [psd-tools](https://github.com/psd-tools/psd-tools).

[![PyPI Version](https://img.shields.io/pypi/v/psd2svg.svg)](https://pypi.python.org/pypi/psd2svg)
[![Documentation Status](https://readthedocs.org/projects/psd2svg/badge/?version=latest)](https://psd2svg.readthedocs.io/en/latest/?badge=latest)

## Install

Use `pip` to install:

```bash
pip install psd2svg
```

### Platform Support

**Supported Platforms:**

- **Linux**: Full support for all features including text layer conversion
- **macOS**: Full support for all features including text layer conversion
- **Windows**: Supported - text layers are rasterized as images

**Text Layer Conversion:**

Text layer conversion requires the `fontconfig` library, which is automatically installed on Linux and macOS but not available on Windows:

- **Linux/macOS**: Text layers are converted to native SVG `<text>` elements (fontconfig installed automatically)
- **Windows**: Text layers are automatically rasterized as images (fontconfig not available on Windows)
- **All platforms**: Can explicitly disable text conversion with `enable_text=False`

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

### Command Line Options

**Image handling:**

- `--image-prefix PATH` - Save extracted images to external files with this prefix, relative to the output SVG file's directory (default: embed images)
- `--image-format FORMAT` - Image format for rasterized layers: webp, png, jpeg (default: webp)

**Feature flags:**

- `--no-text` - Disable text layer conversion (rasterize text instead)
- `--no-live-shapes` - Disable live shape conversion (use paths instead of shape primitives)
- `--no-title` - Disable insertion of `<title>` elements with layer names

**Text adjustment:**

- `--text-letter-spacing-offset OFFSET` - Global offset (in pixels) to add to letter-spacing values (default: 0.0)

**Examples:**

```bash
# Export images to same directory as SVG (using "." prefix)
psd2svg input.psd output.svg --image-prefix .
# => output.svg, 01.webp, 02.webp, ...

# Export images to subdirectory
psd2svg input.psd output/result.svg --image-prefix images/img
# => output/result.svg, output/images/img01.webp, output/images/img02.webp, ...

# Export images as PNG
psd2svg input.psd output.svg --image-prefix . --image-format png
# => output.svg, 01.png, 02.png, ...

# Disable text layer conversion
psd2svg input.psd output.svg --no-text

# Compact output: disable titles and use paths
psd2svg input.psd output.svg --no-title --no-live-shapes
```

## API

### Simple conversion

The package provides a simple `convert()` function for quick conversions:

```python
from psd2svg import convert

# Convert PSD to SVG with embedded images
convert('input.psd', 'output.svg')

# Convert with external images in same directory as SVG
convert('input.psd', 'output.svg', image_prefix='.')
# => output.svg, 01.webp, 02.webp, ...

# Convert with external images in subdirectory (relative to output SVG)
convert('input.psd', 'output.svg', image_prefix='images/img')
# => output.svg, images/img01.webp, images/img02.webp, ...

# Convert with external PNG images
convert('input.psd', 'output.svg', image_prefix='images/img', image_format='png')
# => output.svg, images/img01.png, images/img02.png, ...

# Disable text layer conversion (rasterize text instead)
convert('input.psd', 'output.svg', enable_text=False)

# Disable live shapes (use paths instead)
convert('input.psd', 'output.svg', enable_live_shapes=False)

# Disable title elements and adjust letter spacing
convert('input.psd', 'output.svg', enable_title=False, text_letter_spacing_offset=-0.015)
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

# Save to file with external images (relative to output SVG)
document.save("output.svg", image_prefix="images/img", image_format="png")

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

The package includes two rasterizer options for converting SVG to PIL Image:

#### ResvgRasterizer (Default)

Fast, production-ready rasterizer using resvg (included as dependency):

```python
from psd2svg import SVGDocument
from psd2svg.rasterizer import ResvgRasterizer

document = SVGDocument.from_psd(psdimage)

# Built-in rasterize method (uses ResvgRasterizer by default)
image = document.rasterize()
image.save('output.png')

# Rasterize with custom DPI for higher resolution
image = document.rasterize(dpi=300)
image.save('output_high_res.png')

# Or use rasterizer directly
rasterizer = ResvgRasterizer(dpi=96)
svg_string = document.tostring(embed_images=True)
image = rasterizer.from_string(svg_string)
image.save('output.png')
```

**Note:** resvg-py may crash (SIGABRT) on malformed SVG or missing files instead of raising Python exceptions. For production use, validate SVG content before rasterizing. See the [Rasterizers Guide](https://psd2svg.readthedocs.io/en/latest/rasterizers.html#known-issues-with-resvg-py) for workarounds.

#### PlaywrightRasterizer (Optional)

Browser-based rasterizer with better SVG 2.0 support and more graceful error handling:

```python
from psd2svg import SVGDocument
from psd2svg.rasterizer import PlaywrightRasterizer

document = SVGDocument.from_psd(psdimage)

# Use PlaywrightRasterizer for better vertical text support
with PlaywrightRasterizer(dpi=96) as rasterizer:
    image = document.rasterize(rasterizer=rasterizer)
    image.save('output.png')
```

**Installation:**

```bash
pip install psd2svg[browser]
# or with uv:
uv sync --group browser

# Install Chromium browser
playwright install chromium
```

**Platform Support:** Playwright supports Linux, macOS, and Windows. Browsers are automatically downloaded during installation.

**When to use:**

- **ResvgRasterizer** (default): Production use, batch processing, fast rendering
- **PlaywrightRasterizer**: Testing SVG 2.0 features, vertical text with `text-orientation: upright`, quality assurance

See the [Rasterizers documentation](https://psd2svg.readthedocs.io/en/latest/rasterizers.html) for complete details.

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
