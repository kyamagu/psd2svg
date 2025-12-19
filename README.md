# PSD2SVG

PSD to SVG converter based on [psd-tools](https://github.com/psd-tools/psd-tools).

[![PyPI Version](https://img.shields.io/pypi/v/psd2svg.svg)](https://pypi.python.org/pypi/psd2svg)
[![Documentation Status](https://readthedocs.org/projects/psd2svg/badge/?version=latest)](https://psd2svg.readthedocs.io/en/latest/?badge=latest)

## Features

- Convert PSD files to clean, editable SVG
- Preserve layers, groups, and artboards
- Convert text layers to native SVG text elements (experimental)
- Smart font matching with Unicode codepoint-based selection
- Support for blending modes, effects, and vector shapes
- Adjustment layers support (Invert, Posterize, Threshold, HueSaturation, Exposure, BrightnessContrast)
- Optional font subsetting for web optimization (90%+ size reduction with WOFF2)
- Command-line tool and Python API

## Installation

```bash
pip install psd2svg
```

### Optional Features

```bash
# Browser-based rasterization (better SVG 2.0 support)
pip install psd2svg[browser]
playwright install chromium
```

## Quick Start

### Command Line

```bash
# Basic conversion
psd2svg input.psd output.svg

# With external images
psd2svg input.psd output.svg --image-prefix images/img
```

### Python API

```python
from psd2svg import convert

# Simple conversion with embedded images
convert('input.psd', 'output.svg')

# With external images
convert('input.psd', 'output.svg', image_prefix='images/img')
```

### Advanced Usage

```python
from psd_tools import PSDImage
from psd2svg import SVGDocument

# Load PSD and create SVG document
psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)

# Save with options
document.save("output.svg", embed_images=True)

# Embed and subset fonts for web
document.save("output.svg", embed_fonts=True, font_format="woff2")

# Rasterize to PNG
image = document.rasterize()
image.save('output.png')
```

## Platform Support

- **Linux/macOS**: Full support including text layer conversion and font embedding
- **Windows**: Full support including text layer conversion and font embedding

Text layer conversion uses a hybrid approach:

1. **Static font mapping** (~4,950 fonts: 539 default + 370 Hiragino + 4,042 Morisawa) - works on all platforms
2. **Platform-specific font resolution** for font file discovery when embedding fonts:
   - **Linux/macOS**: fontconfig
   - **Windows**: Windows registry + fontTools parsing

For fonts not in the default mapping, you can provide custom font mappings. See the [Font Handling documentation](https://psd2svg.readthedocs.io/en/latest/fonts.html#custom-font-mapping) for details.

## Security

When processing untrusted PSD files, follow security best practices:

- **File size limits**: Validate file size before processing to prevent memory exhaustion
- **Timeout protection**: Implement conversion timeouts to prevent CPU exhaustion
- **Path validation**: Validate all file paths, especially when using `image_prefix`
- **Sandboxing**: Run conversions in isolated environments for untrusted input

psd2svg includes security features:

- Path traversal protection in `image_prefix` parameter
- Font file validation in rasterizers
- Automated dependency vulnerability scanning

See [Security Documentation](https://psd2svg.readthedocs.io/en/latest/security.html) for detailed guidance and [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## Documentation

Full documentation is available at **[psd2svg.readthedocs.io](https://psd2svg.readthedocs.io/)**

Topics covered:

- [Getting Started Guide](https://psd2svg.readthedocs.io/)
- [Command Line Options](https://psd2svg.readthedocs.io/)
- [Python API Reference](https://psd2svg.readthedocs.io/)
- [Font Subsetting & Web Optimization](https://psd2svg.readthedocs.io/)
- [Rasterization Options](https://psd2svg.readthedocs.io/)
- [Text Layer Support](https://psd2svg.readthedocs.io/)
- [Known Limitations](https://psd2svg.readthedocs.io/)

## Development

```bash
# Install dependencies
uv sync

# Optional: Install browser support for PlaywrightRasterizer
uv sync --extra browser
uv run playwright install chromium

# Run tests
uv run pytest

# Run type checking and linting
uv run mypy src/ tests/
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

See [CLAUDE.md](CLAUDE.md) for detailed development instructions.

## Known Limitations

- SVG 1.1 does not support all Photoshop blending modes
- Filter effects are approximations
- Some adjustment layers not yet implemented (Curves, Levels, etc.)
- Smart object filters not implemented
- APIs are not thread-safe

See the [full documentation](https://psd2svg.readthedocs.io/) for complete details and workarounds.

## License

MIT License - see LICENSE file for details.
