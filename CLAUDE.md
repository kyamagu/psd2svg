# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Platform Support

**Supported Platforms:**

* **Linux**: Full support for all features including text layer conversion
* **macOS**: Full support for all features including text layer conversion
* **Windows**: Supported - text layers are rasterized as images (fontconfig not available)

**Text Layer Conversion:**

Text layer conversion requires fontconfig, which is automatically installed on Linux and macOS but not available on Windows:

* **Linux/macOS**: Text layers are converted to native SVG `<text>` elements (fontconfig installed automatically)
* **Windows**: Text layers are automatically rasterized as images (fontconfig not available on Windows)
* **All platforms**: Can explicitly disable text conversion with `enable_text=False`

Both ResvgRasterizer and PlaywrightRasterizer support all three platforms for SVG rasterization.

## Commands

### Development and Testing

- `uv run pytest` - Run tests
- `uv run mypy src/ tests/` - Run type checking
- `uv run ruff check src/ tests/` - Run linting
- `uv run ruff format src/ tests/` - Format code
- `uv run python` - Run python interpreter

### Building and Installation

- `uv sync` - Install dependencies
- `uv sync --group docs` - Install documentation dependencies
- `uv sync --group browser` - Install browser-based rasterizer dependencies (Playwright)
- `uv sync --group fonts` - Install font subsetting dependencies (fonttools)
- `uv run playwright install chromium` - Install Chromium browser for Playwright (after installing browser group)
- `uv build` - Build distribution packages

### Documentation

- `uv run sphinx-build -b html docs docs/_build/html` - Build HTML documentation
- `uv run sphinx-build -b html docs docs/_build/html -W` - Build with warnings as errors
- Open `docs/_build/html/index.html` in browser to view documentation

### Command Line Usage

- `psd2svg input.psd output.svg` - Convert PSD to SVG

### Advanced Options

#### Text Letter Spacing Offset

Photoshop and SVG renderers may have slightly different default letter spacing due to differences in kerning algorithms. You can compensate for these differences using the `text_letter_spacing_offset` parameter:

```python
from psd2svg import SVGDocument
from psd_tools import PSDImage

psdimage = PSDImage.open("input.psd")

# Apply a small negative offset to tighten letter spacing
document = SVGDocument.from_psd(
    psdimage,
    text_letter_spacing_offset=-0.015  # in pixels
)

# Or use convert() function
from psd2svg import convert
convert('input.psd', 'output.svg', text_letter_spacing_offset=-0.015)
```

The offset is in pixels and is added to all letter-spacing values. Typical values range from -0.02 to 0.02. Experiment with different values to match your specific fonts and target renderers.

#### Font Embedding

When saving SVG files or using PlaywrightRasterizer, you can embed fonts as base64 data URIs using `@font-face` CSS rules. This ensures fonts are available for browser-based rendering:

```python
from psd2svg import SVGDocument
from psd2svg.rasterizer import PlaywrightRasterizer
from psd_tools import PSDImage

psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)

# Option 1: Save SVG with embedded fonts (large file size)
document.save('output.svg', embed_images=True, embed_fonts=True)

# Option 2: Get string with embedded fonts
svg_string = document.tostring(embed_images=True, embed_fonts=True)

# Option 3: PlaywrightRasterizer auto-embeds fonts (recommended)
with PlaywrightRasterizer(dpi=96) as rasterizer:
    # Fonts are automatically embedded for browser rendering
    image = document.rasterize(rasterizer=rasterizer)
    image.save('output.png')
```

**When to use font embedding:**

- **PlaywrightRasterizer**: Fonts are automatically embedded (no manual action needed)
- **Saving SVG for web**: Use `embed_fonts=True` to ensure fonts display correctly in browsers
- **Debugging**: Keep `embed_fonts=False` (default) for smaller, more readable SVG files

**Important Notes:**

- Font embedding significantly increases file size (100KB+ per font)
- Fonts are cached per SVGDocument instance to avoid re-encoding
- Missing/unreadable fonts are logged as warnings but don't fail the operation
- ResvgRasterizer passes font files directly (more efficient than embedding)

**⚠️ Font License Considerations:**

Font embedding may be subject to licensing restrictions. Before distributing SVG files with embedded fonts, ensure you have the appropriate license rights:

- **Commercial fonts**: Check if your license permits embedding/redistribution
- **Open source fonts**: Verify the license (e.g., OFL, Apache) allows embedding
- **System fonts**: May have restrictions on redistribution
- **Web use**: Some fonts require web-specific licenses for embedding

**Recommended practices:**

- Use font embedding only for internal/testing purposes unless you have proper licenses
- For production web use, consider using web fonts (Google Fonts, Adobe Fonts, etc.)
- For PlaywrightRasterizer (rasterization only), font embedding is typically acceptable as it produces images, not redistributable font files
- Consult with legal counsel if uncertain about font license compliance

#### Font Subsetting and WOFF2 Conversion

For web delivery, you can drastically reduce embedded font file sizes (typically 90%+ reduction) using font subsetting and WOFF2 compression. This feature requires the optional `fonts` dependency group:

```bash
uv sync --group fonts
```

**Basic Usage:**

```python
from psd2svg import SVGDocument
from psd_tools import PSDImage

psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)

# Option 1: WOFF2 format (auto-enables subsetting, best compression)
document.save('output.svg', embed_images=True, embed_fonts=True, font_format='woff2')

# Option 2: Explicit subsetting with TTF format
document.save('output.svg', embed_images=True, embed_fonts=True, subset_fonts=True)

# Option 3: Full control over format and subsetting
document.save(
    'output.svg',
    embed_images=True,
    embed_fonts=True,
    subset_fonts=True,
    font_format='woff2'  # 'ttf', 'otf', or 'woff2'
)
```

**Supported Formats:**

- `'ttf'` - TrueType (default, no subsetting unless explicitly enabled)
- `'otf'` - OpenType (no subsetting unless explicitly enabled)
- `'woff2'` - Web Open Font Format 2 (best compression, auto-enables subsetting)

**How It Works:**

1. **Unicode Extraction**: Analyzes all `<text>` and `<tspan>` elements to determine which characters are actually used
2. **Font Subsetting**: Uses `fonttools` (pyftsubset) to create minimal font files containing only the required glyphs
3. **Format Conversion**: Optionally converts fonts to WOFF2 for maximum compression
4. **Embedding**: Embeds the subset fonts as base64 data URIs in `@font-face` CSS rules

**Performance Benefits:**

- **File Size**: 90-95% reduction typical (e.g., 150KB → 10KB per font)
- **Load Time**: Significantly faster page loads for SVG files displayed in browsers
- **Bandwidth**: Reduced data transfer costs for web applications

**Requirements and Notes:**

- Requires `fonttools[woff]>=4.50.0` (install with `uv sync --group fonts`)
- `subset_fonts=True` requires `embed_fonts=True` (raises `ValueError` otherwise)
- `font_format='woff2'` automatically enables subsetting (most efficient option)
- Missing characters fall back to full font encoding with a warning
- Font subsetting is cached per SVGDocument instance to avoid re-processing

**When to Use Font Subsetting:**

- ✅ **Web delivery**: Embedding SVG files in web pages or applications
- ✅ **Email**: Embedding SVG in HTML emails (smaller = better deliverability)
- ✅ **Documentation**: Generating documentation with embedded fonts
- ❌ **Editing**: Keep `subset_fonts=False` if SVG will be edited (may need additional characters)
- ❌ **Unknown content**: Don't subset if text content might change later

**Example - Complete Workflow:**

```python
from psd2svg import SVGDocument
from psd_tools import PSDImage

# Load PSD
psdimage = PSDImage.open("design.psd")
document = SVGDocument.from_psd(psdimage)

# For web deployment - maximum compression
document.save(
    'web/design.svg',
    embed_images=True,
    embed_fonts=True,
    font_format='woff2'  # Auto-enables subsetting
)

# For editing - keep fonts external
document.save(
    'edit/design.svg',
    embed_fonts=False,  # External fonts
    image_prefix='images/design'
)

# For archiving - full embedded fonts
document.save(
    'archive/design.svg',
    embed_images=True,
    embed_fonts=True,
    font_format='ttf'  # No subsetting
)
```

**Font License Considerations (Subsetting):**

Font subsetting creates derivative font files. Ensure your font license permits:

- Subsetting and modification of font files
- Distribution of subset fonts (even if embedded in SVG)
- WOFF2 conversion (format transformation)

Most open-source fonts (OFL, Apache) explicitly allow subsetting. Commercial fonts vary - check your license agreement.

#### Text Wrapping

For bounding box text (ShapeType=1), you can enable text wrapping using `<foreignObject>` with XHTML/CSS:

```python
from psd2svg import SVGDocument
from psd2svg.core.text import TextWrappingMode
from psd_tools import PSDImage

psdimage = PSDImage.open("input.psd")

# Enable foreignObject text wrapping for bounding box text
document = SVGDocument.from_psd(
    psdimage,
    text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
)

document.save('output.svg')

# Or use the convert() function
from psd2svg import convert
convert('input.psd', 'output.svg', text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT)
```

**How it works:**

- Bounding box text (ShapeType=1) is rendered as `<foreignObject>` containing XHTML `<div>`, `<p>`, and `<span>` elements
- CSS styling provides natural text wrapping within the bounding box
- Point text (ShapeType=0) always uses native SVG `<text>` elements regardless of this setting

**When to use foreignObject wrapping:**

- ✅ Bounding box text with long paragraphs that need to wrap
- ✅ When targeting modern browsers (Chrome, Firefox, Safari, Edge)
- ✅ For web-only SVG display
- ✅ When using PlaywrightRasterizer for rasterization (browser-based)

**Limitations:**

- ❌ Not supported by ResvgRasterizer (resvg/resvg-py cannot render foreignObject elements)
- ❌ Not supported by many SVG renderers (PDF converters, design tools like Sketch/Figma, Inkscape)
- ❌ Text cannot be edited in vector graphics editors (appears as embedded HTML)
- ❌ Some advanced text features may have subtle rendering differences vs. native SVG
- ❌ Point text (ShapeType=0) always uses native SVG `<text>` elements

**Default behavior:**

By default, text wrapping is disabled (`TextWrappingMode.NONE`). Bounding box text uses native SVG `<text>` elements without wrapping.

## CI/CD

### Automated Testing

The repository uses GitHub Actions for continuous integration:

- **Test Workflow** (`.github/workflows/test.yml`): Runs on every push and pull request
  - Tests across Python 3.10, 3.11, 3.12, 3.13, and 3.14
  - Executes linting (ruff), type checking (mypy), and unit tests (pytest)
  - Uses uv for fast dependency management
  - Installs required fonts (MS Core Fonts and Noto fonts) for text rendering tests

#### Font Requirements for Testing

The test suite includes tests for non-Latin text rendering that require specific fonts:

**Core fonts (always installed in CI):**

- MS Core Fonts (Arial, Times New Roman, etc.)
- Noto Sans (baseline Latin)
- Noto Sans CJK (includes Noto Sans JP, Noto Sans KR, Noto Sans SC, Noto Sans TC for Japanese/Korean/Chinese)

**Optional fonts (tests skipped if unavailable):**

- Noto Sans Arabic (right-to-left script)
- Noto Sans Devanagari (Indic script)
- Noto Sans Thai (complex shaping)
- Noto Sans Hebrew (right-to-left script)

**Local development setup:**

On Ubuntu/Debian:

```bash
sudo apt-get install fonts-noto-core fonts-noto-cjk fonts-noto-ui-core
sudo fc-cache -fv
```

On macOS:

```bash
brew tap homebrew/cask-fonts
brew install --cask font-noto-sans font-noto-sans-cjk-jp
```

**Pytest markers:**

Tests requiring specific fonts use markers like `@requires_noto_sans_jp` or `@requires_noto_sans_cjk`. These tests are automatically skipped if fonts are unavailable. See [tests/conftest.py](tests/conftest.py) for available markers and the full list of supported fonts.

### Pull Request Workflow

**IMPORTANT:** Always run formatting and type checking before pushing to remote to ensure CI tests pass.

**Pre-push checklist:**

1. **Format code:**

   ```bash
   uv run ruff format src/ tests/
   ```

2. **Run linting:**

   ```bash
   uv run ruff check src/ tests/
   ```

3. **Run type checking:**

   ```bash
   uv run mypy src/ tests/
   ```

4. **Run tests:**

   ```bash
   uv run pytest
   ```

5. **Stage and commit changes:**

   ```bash
   git add .
   git commit -m "Your commit message"
   ```

6. **Push to remote:**

   ```bash
   git push -u origin your-branch-name
   ```

7. **Create pull request:**

   ```bash
   gh pr create --title "Your PR title" --body "PR description"
   ```

**Complete workflow example:**

```bash
# Make your changes
# ...

# Format and check code
uv run ruff format src/ tests/
uv run ruff check src/ tests/
uv run mypy src/ tests/
uv run pytest

# Commit and push
git add .
git commit -m "Add feature X"
git push -u origin feature/x

# Create PR
gh pr create --title "Add feature X" --body "Description of feature X"
```

**Why this matters:**

The CI workflow runs these same checks on every push and PR. Running them locally first:

- Catches issues before pushing (faster feedback)
- Avoids failed CI checks that require additional commits
- Keeps the git history clean
- Saves CI resources

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
- `resvg_rasterizer.py` - Production-ready resvg-based renderer (default implementation)
- `playwright_rasterizer.py` - Optional browser-based renderer using Playwright (requires `browser` dependency group)

The default rasterizer uses the resvg library via resvg-py for fast, accurate SVG to raster image conversion. The optional PlaywrightRasterizer provides browser-based rendering for advanced SVG 2.0 features.

### Rasterizer API

The `BaseRasterizer` abstract class defines a clean interface for SVG rasterization:

**Public Methods:**

- `from_file(filepath: str) -> Image.Image` - Rasterize an SVG file
- `from_string(svg_content: Union[str, bytes]) -> Image.Image` - Rasterize SVG content from string/bytes

**Protected Methods:**

- `_composite_background(image: Image.Image) -> Image.Image` - Utility for normalizing alpha channel

**Usage Examples:**

Default resvg rasterization (fast, production-ready):

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

Browser-based rasterization (better SVG 2.0 support, slower):

```python
from psd2svg.rasterizer import PlaywrightRasterizer

# Requires: uv sync --group browser && uv run playwright install chromium

# Create browser rasterizer
with PlaywrightRasterizer(dpi=96) as rasterizer:
    image = rasterizer.from_file('input.svg')
    image.save('output.png')

# Or use with SVGDocument
from psd2svg import SVGDocument
from psd_tools import PSDImage

psdimage = PSDImage.open('input.psd')
document = SVGDocument.from_psd(psdimage)

# Rasterize with browser (better vertical text support)
with PlaywrightRasterizer(dpi=96) as rasterizer:
    image = document.rasterize(rasterizer=rasterizer)
    image.save('output.png')
```

**When to use PlaywrightRasterizer:**

- Testing/validation of advanced SVG features (vertical text, text-orientation, dominant-baseline)
- SVG 2.0 features not supported by resvg
- Quality assurance against browser rendering
- Comparing rendering output with browser behavior

**When to use ResvgRasterizer (default):**

- Production rasterization (faster, no external dependencies)
- Batch processing
- Server deployments
- Standard SVG features

### Dependencies

- `psd-tools>=1.12.0` - PSD file parsing
- `pillow` - Image processing
- `numpy` - Numerical operations
- `resvg-py` - SVG rasterization (production-ready)
- `fontconfig-py` - Font resolution for text layers

### Code Quality

- **Type hints**: Full type annotation coverage with mypy support
  - TODO: Enable stricter mypy checks (`warn_return_any`) after adding complete type annotations
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

### Known Issues

#### resvg-py Variable Font Rendering Bug

**Issue**: resvg-py (Python wrapper for resvg) does not correctly apply `font-weight` attributes when rendering variable fonts. It may render text at the wrong weight (e.g., thin instead of regular/400).

**Workaround**: The converter uses numeric `font-weight` values (100-900) instead of keywords for non-regular weights. Regular weight (400) is omitted since it's the SVG default. However, resvg-py may still not render variable fonts correctly.

**Impact**:

- SVG files display correctly in browsers (Chrome, Firefox, Safari)
- Rasterized output via resvg-py may show incorrect font weights
- Affects variable fonts like `NotoSansJP-VariableFont_wght.ttf`

**Status**: This is a bug in the resvg-py wrapper library, not in psd2svg. Monitor upstream: <https://github.com/sparkfish/resvg-py>

**Recommendation**: For production rasterization with variable fonts, consider:

1. Using browser-based rendering (Chromium headless) instead of resvg-py
2. Installing static (non-variable) font variants
3. Testing rasterized output to verify font weight rendering

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
