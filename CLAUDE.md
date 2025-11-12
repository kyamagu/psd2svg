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

**Rasterizers** (`src/psd2svg/rasterizer/`):

- `base_rasterizer.py` - Abstract base class
- `resvg_rasterizer.py` - Resvg-based renderer (recommended)
- `chromium_rasterizer.py` - Chrome/Chromium-based rendering
- `batik_rasterizer.py` - Apache Batik renderer
- `inkscape_rasterizer.py` - Inkscape-based rendering

### Dependencies

- `psd-tools>=1.10.13` - PSD file parsing
- `pillow` - Image processing
- `numpy` - Numerical operations

### Code Quality

- **Type hints**: Full type annotation coverage with mypy support
- **Linting**: Ruff for fast linting and formatting
- **Python 3.10+**: Modern Python with no legacy compatibility code

### Limitations

- SVG 1.1 doesn't support all Photoshop blending modes
- Filter effects are approximations
- Most adjustment layers not implemented
- Smart object filters not supported
- APIs are NOT thread-safe
