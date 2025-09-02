# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development and Testing
- `uv run --extra test pytest` - Run tests with uv
- `uv run --extra test mypy src/` - Run type checking with mypy
- `uv run --extra test ruff check src/` - Run linting with ruff
- `uv run --extra test ruff format src/` - Format code with ruff
- `uv sync --extra test` - Install with test dependencies
- `uv run pytest` - Run tests (after sync)
- `uv run mypy src/` - Run type checking (after sync)
- `uv run ruff check src/` - Run linting (after sync)
- `uv run ruff format src/` - Format code (after sync)

### Building and Installation
- `uv sync` - Install dependencies
- `uv build` - Build distribution packages
- `pip install -e .` - Install in development mode (fallback)

### Command Line Usage
- `psd2svg input.psd output.svg` - Convert PSD to SVG
- `psd2svg input.psd output/` - Convert with directory output
- `psd2svg input.psd output.svg --resource-path .` - Export PNG resources
- `psd2svg input.psd output.png --rasterizer chromium` - Convert to raster format

## Architecture

### Core Structure
The package follows a modular converter architecture with multiple inheritance:

- **Main Converter (`PSD2SVG` class)**: Inherits from multiple converter mixins:
  - `AdjustmentsConverter` - Handles adjustment layers
  - `EffectsConverter` - Processes layer effects
  - `LayerConverter` - Core layer conversion logic
  - `PSDReader` - Handles input from various sources (files, URLs, streams)
  - `ShapeConverter` - Converts vector shapes
  - `SVGWriter` - Handles SVG output generation
  - `TextConverter` - Processes text layers

### Key Components

**Converter Pipeline** (`src/psd2svg/converter/`):
- `core.py` - Main layer conversion logic, handles different layer types
- `io.py` - Input/output handling for files, URLs, and storage backends
- `shape.py` - Vector shape processing
- `text.py` - Text layer rendering
- `effects.py` - Layer effects and blending modes
- `adjustments.py` - Color adjustments (mostly unimplemented)


**Rasterizers** (`src/psd2svg/rasterizer/`):
- `base_rasterizer.py` - Abstract base class
- `chromium_rasterizer.py` - Chrome/Chromium-based rendering
- `batik_rasterizer.py` - Apache Batik renderer  
- `inkscape_rasterizer.py` - Inkscape-based rendering

### Dependencies
- `psd-tools>=1.8.11` - PSD file parsing
- `svgwrite` - SVG generation
- `pillow` - Image processing
- `numpy` - Numerical operations

### Code Quality
- **Type hints**: Full type annotation coverage with mypy support
- **Linting**: Ruff for fast linting and formatting
- **Python 3.9+**: Modern Python with no legacy compatibility code

### Limitations
- SVG 1.1 doesn't support all Photoshop blending modes
- Filter effects are approximations
- Most adjustment layers not implemented
- Smart object filters not supported
- APIs are NOT thread-safe