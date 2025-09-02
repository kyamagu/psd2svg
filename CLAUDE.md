# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development and Testing
- `pytest` - Run tests
- `pip install -e .` - Install in development mode

### Building and Installation
- `pip install -e .` - Install in development mode
- `python -m build` - Build distribution packages

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
- `future` - Python 2/3 compatibility

### Limitations
- SVG 1.1 doesn't support all Photoshop blending modes
- Filter effects are approximations
- Most adjustment layers not implemented
- Smart object filters not supported
- APIs are NOT thread-safe