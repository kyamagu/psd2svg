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

## CI/CD

### Automated Testing

The repository uses GitHub Actions for continuous integration:

- **Test Workflow** (`.github/workflows/test.yml`): Runs on every push and pull request
  - Tests across Python 3.10, 3.11, 3.12, 3.13, and 3.14
  - Executes linting (ruff), type checking (mypy), and unit tests (pytest)
  - Uses uv for fast dependency management

### Release Process

Releases are automated via GitHub Actions:

- **Release Workflow** (`.github/workflows/release.yml`): Triggered by version tags
  - Tag format: `v*` (e.g., `v0.3.0`, `v1.0.0`)
  - Automatically builds distribution packages
  - Publishes to PyPI using trusted publishing (OIDC)
  - Creates GitHub releases with auto-generated notes

**To create a release:**

```bash
git tag v0.3.0
git push origin v0.3.0
```

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
  - `TextConverter` - Processes text layers

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

- `psd-tools>=1.12.0` - PSD file parsing
- `pillow` - Image processing
- `numpy` - Numerical operations
- `resvg-py` - SVG rasterization (production-ready)
- `fontconfig-py` - Font resolution for text layers

### Code Quality

- **Type hints**: Full type annotation coverage with mypy support
  - TODO: Enable stricter mypy checks (`disallow_untyped_defs`, `warn_return_any`) after adding complete type annotations
  - Current configuration ignores psd_tools import errors (lacks type stubs)
- **Linting**: Ruff for fast linting and formatting
- **Python 3.10+**: Modern Python with no legacy compatibility code
- **Abstract base classes**: Proper use of ABC for interface definitions

### Limitations

- SVG 1.1 doesn't support all Photoshop blending modes
- Filter effects are approximations
- Most adjustment layers not implemented
- Smart object filters not supported
- APIs are NOT thread-safe

### Experimental Features

#### Text Layer Conversion

Text layer conversion to SVG `<text>` elements is **experimental** and enabled by default. It can be disabled via the `enable_text` flag:

```python
from psd2svg.core.converter import Converter

converter = Converter(psdimage, enable_text=False)  # Falls back to rasterization
```

**Supported Features:**

- Text content with multiple paragraphs and styled spans
- Font family, size, weight (bold), and style (italic)
- Faux bold and faux italic
- Font color (solid fill and stroke colors)
- Horizontal and vertical writing modes
- Text alignment (left, center, right, justify)
- Text decoration (underline, strikethrough)
- Text transformation (all-caps, small-caps)
- Superscript and subscript with accurate positioning
- Baseline shift for custom vertical positioning
- Letter spacing (tracking)
- Line height (leading)
- Horizontal and vertical text scaling
- Position, rotation, and scaling transformations

**Current Limitations:**

- Text wrapping for bounding box mode (ShapeType=1) not supported
- Transform matrices not fully implemented
- Only solid fill/stroke colors supported (no gradients or patterns)
- Line height uses approximate calculation for auto-leading
- Requires fonts to be installed on the system (uses `fontconfig` for font resolution)
- Cross-platform font availability may vary
- Kerning and ligatures not supported
- Horizontal/vertical text scaling uses SVG 2.0 features (may not work in older renderers)

**Font Requirements:**

Text conversion requires fonts to be installed on the system. When fonts are not available, a warning is logged and the text may fall back to a default system font.

**Renderer Compatibility:**

SVG text rendering quality varies across renderers. Chromium-based browsers provide the best support, including for vertical text features. The bundled resvg rasterizer does not support `text-orientation: upright` or `dominant-baseline` for vertical text.
