# PSD2SVG

PSD to SVG converter based on [psd-tools](https://github.com/psd-tools/psd-tools).

[![PyPI Version](https://img.shields.io/pypi/v/psd2svg.svg)](https://pypi.python.org/pypi/psd2svg)

## Install

Use `pip` to install:

```bash
pip install psd2svg
```

## Usage (v0.2.0)

The package comes with a command-line tool:

```bash
psd2svg input.psd output.svg
```

When the output path is a directory, or omitted, the tool infers the output name from the input:

```bash
psd2svg input.psd output/  # => output/input.svg
psd2svg input.psd          # => input.svg
```

When `--resource-path` flag is specified, all png resources are exported to the path specified by `--resource-path`:

```bash
psd2svg input.psd output.svg --resource-path .
# => output.svg, xxx1.png, ...

psd2svg input.psd output/ --resource-path .
# => output/input.svg, output/xxx1.png, ...

psd2svg input.psd output/ --resource-path=resources/
# => output/input.svg, output/resources/xxx1.png, ...

psd2svg input.psd svg/ --resource-path=../png/
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

# Rasterize to PIL Image (requires resvg or other rasterizer)
image = document.rasterize()
image.save('output.png')

# Export and load back
exported = document.export()
document = SVGDocument.load(exported["svg"], exported["images"])
```

### Rasterization

The package includes rasterizer support to convert SVG to PIL Image:

```python
from psd2svg import SVGDocument

document = SVGDocument.from_psd(psdimage)

# Built-in rasterize method (uses resvg by default)
image = document.rasterize()

# Or use rasterizer directly
from psd2svg.rasterizer import create_rasterizer

rasterizer = create_rasterizer('resvg')  # or 'chromium', 'batik', 'inkscape'
svg_string = document.tostring(embed_images=True)
image = rasterizer.rasterize_from_string(svg_string)
image.save('output.png')
```

Rasterizers require external dependencies:
- `resvg`: Recommended, fast and accurate (install via `cargo install resvg`)
- `chromium`: Requires Selenium + ChromeDriver
- `batik`: Requires Apache Batik
- `inkscape`: Requires Inkscape

## Test

Run tests with pytest:

```bash
pytest
```

## Notes

* SVG 1.1 does not cover all the blending modes in Photoshop (e.g., `linear-dodge`)
* Filter effects are approximation. Some effects are not implemented.
* Most of adjustments layers are not implemented.
* Smart object filters are not implemented.
* Browser support: SVG rendering quality greatly differs depending on the browser. Chrome tends to be the best quality.
* APIs of this tool is NOT thread-safe.