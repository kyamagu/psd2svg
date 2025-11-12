# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development and Testing

- `uv run pytest` - Run tests
- `uv run mypy src/` - Run type checking
- `uv run ruff check src/` - Run linting
- `uv run ruff format src/` - Format code
- `uv run python` - Run python interpreter

### Building and Installation

- `uv sync` - Install dependencies
- `uv sync --group docs` - Install documentation dependencies
- `uv build` - Build distribution packages

### Documentation

- `uv run sphinx-build -b html docs docs/_build/html` - Build HTML documentation
- `uv run sphinx-build -b html docs docs/_build/html -W` - Build with warnings as errors
- Open `docs/_build/html/index.html` in browser to view documentation

### Command Line Usage

- `psd2svg input.psd output.svg` - Convert PSD to SVG

## Architecture

### Public API

- **`SVGDocument`**: Main class for working with SVG documents and their resources
- **`convert()`**: Convenience function for simple PSD to SVG conversions

### Core Structure

The package follows a modular converter architecture with multiple inheritance:

- **Internal Converter (`Converter` class)**: Inherits from multiple converter mixins:
  - `AdjustmentConverter` - Handles adjustment layers
  - `EffectConverter` - Processes layer effects
  - `LayerConverter` - Core layer conversion logic
  - `PaintConverter` - Handles painting logic
  - `ShapeConverter` - Converts vector shapes
  - `TypeConverter` - Processes typographic layers

### Key Components

**Core** (`src/psd2svg/core/`): Core converter implementations (internal).

**Public Modules** (`src/psd2svg/`):

- `svg_document.py` - SVGDocument class and convert() function
- `svg_utils.py` - SVG manipulation utilities
- `image_utils.py` - Image encoding/decoding utilities
- `eval.py` - Quality evaluation utilities for testing

**Rasterizer** (`src/psd2svg/rasterizer/`):

- `base_rasterizer.py` - Abstract base class defining the rasterizer interface
- `resvg_rasterizer.py` - Production-ready resvg-based renderer (only supported implementation)

The rasterizer uses the resvg library via resvg-py for fast, accurate SVG to raster image conversion.

### Rasterizer API

The `BaseRasterizer` abstract class defines a clean interface for SVG rasterization:

**Public Methods:**

- `from_file(filepath: str) -> Image.Image` - Rasterize an SVG file
- `from_string(svg_content: Union[str, bytes]) -> Image.Image` - Rasterize SVG content from string/bytes

**Protected Methods:**

- `_composite_background(image: Image.Image) -> Image.Image` - Utility for normalizing alpha channel

**Usage Example:**

```python
from psd2svg.rasterizer import ResvgRasterizer

# Create rasterizer with optional DPI setting
rasterizer = ResvgRasterizer(dpi=96)

# Rasterize from file
image = rasterizer.from_file('input.svg')
image.save('output.png')

# Rasterize from string
svg_content = '<svg>...</svg>'
image = rasterizer.from_string(svg_content)
image.save('output.png')
```

### Dependencies

- `psd-tools>=1.10.13` - PSD file parsing
- `pillow` - Image processing
- `numpy` - Numerical operations
- `resvg-py` - SVG rasterization (production-ready)

### Code Quality

- **Type hints**: Full type annotation coverage with mypy support
- **Linting**: Ruff for fast linting and formatting
- **Python 3.10+**: Modern Python with no legacy compatibility code
- **Abstract base classes**: Proper use of ABC for interface definitions

### Limitations

- SVG 1.1 doesn't support all Photoshop blending modes
- Filter effects are approximations
- Most adjustment layers not implemented
- Smart object filters not supported
- APIs are NOT thread-safe
