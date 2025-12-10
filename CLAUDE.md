# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

### Essential Commands

```bash
# Development
uv sync                          # Install dependencies
uv run pytest                    # Run tests
uv run mypy src/ tests/          # Type checking
uv run ruff check src/ tests/    # Linting
uv run ruff format src/ tests/   # Format code

# Optional dependencies
uv sync --group docs             # Documentation tools
uv sync --group browser          # Playwright rasterizer

# Documentation
uv run sphinx-build -b html docs docs/_build/html
```

### Pre-commit Checklist

Before pushing changes, always run:

```bash
uv run ruff format src/ tests/
uv run ruff check src/ tests/
uv run mypy src/ tests/
uv run pytest
```

## Platform Support

- **Linux/macOS**: Full support including text layer conversion and font embedding (fontconfig)
- **Windows**: Full support including text layer conversion and font embedding (Windows registry)
- **Text conversion**: Can be disabled with `enable_text=False` on any platform

### Font Resolution Strategy

#### Background

PSD files store font references as **PostScript names** (e.g., "ArialMT", "HelveticaNeue-Bold"). For SVG output, we need to convert these to **CSS font families** (e.g., "Arial", "Helvetica Neue"). Additionally:

- **When `embed_fonts=False`**: Only family names are needed for the SVG `font-family` attribute
- **When `embed_fonts=True`**: Must locate actual system font files for embedding

#### Architecture: Deferred Resolution

psd2svg uses a **two-phase approach** to optimize performance:

**Phase 1 - PSD Conversion** (`from_psd()`):

- PostScript names stored directly in SVG `font-family` attributes
- No font resolution performed (fast conversion)
- Original PSD intent preserved

**Phase 2 - Output** (`save()`, `tostring()`, `rasterize()`):

- Extract PostScript names from SVG tree
- Resolve to CSS family names based on context:
  - **`embed_fonts=False`**: Use static mapping (fast, no system queries)
  - **`embed_fonts=True`**: Use platform-specific resolution (locates font files)
- Update `font-family` attributes with resolved names
- Embed fonts if requested

#### Resolution Methods

psd2svg provides two distinct resolution methods optimized for different use cases:

**`FontInfo.lookup_static()`** - For font metadata lookup only:

- Resolution chain: Custom mapping → Static mapping (572 fonts) → None
- Returns family name, style, and weight (no file path)
- NO platform-specific queries (no fontconfig/Windows registry)
- Preserves original PostScript names in SVG when fonts not found
- Used when `embed_fonts=False` (prevents unwanted font substitution)
- Fast, cross-platform, no system dependencies

**`FontInfo.resolve()`** - For font file access:

- Resolution chain: Custom mapping → Platform-specific resolution
- Returns complete font metadata including file path
- **Linux/macOS**: fontconfig with CharSet API (fontconfig-py >= 0.4.0)
- **Windows**: Windows registry + fontTools cmap parsing
- Used when `embed_fonts=True` or for rasterization
- May substitute fonts based on system availability

**`FontInfo.find()`** - Backward-compatible wrapper:

- Delegates to `lookup_static()` by default (safe behavior)
- Use `disable_static_mapping=True` to delegate to `resolve()`
- Maintained for backward compatibility; prefer explicit methods in new code

**Custom font mapping**: Users can provide custom mappings via `font_mapping` parameter (always checked first, regardless of method used). See CLI tool: `python -m psd2svg.tools.generate_font_mapping`

#### Charset-Based Font Matching

When resolving fonts, psd2svg analyzes actual text characters for better matching:

1. Extract Unicode characters from text layers
2. Convert to codepoints (e.g., 'あ' → 0x3042)
3. Query system for fonts with best glyph coverage
4. Fallback to name-only matching on errors

**Benefits**: Better selection for multilingual text (CJK, Arabic, etc.), minimal overhead (~10-50ms)

#### Font Embedding Features

**Font Subsetting** (when `embed_fonts=True`):

- Character extraction reused for both charset matching and subsetting
- Typically 90%+ size reduction with WOFF2 format

**Embedding Modes**:

- `tostring()`/`save()`: Data URIs (portable files)
- `rasterize()` with PlaywrightRasterizer: file:// URLs (60-80% faster)

#### Key API Methods

- `TypeSetting.get_postscript_name()`: Extract PostScript name from PSD
- `FontInfo.lookup_static()`: Lookup PostScript name to get font metadata (no platform queries)
- `FontInfo.resolve()`: Resolve PostScript name to font file with platform resolution
- `FontInfo.find()`: Backward-compatible wrapper (delegates to `lookup_static()` or `resolve()`)
- SVG tree is single source of truth for fonts (no separate font list maintained)

## Architecture Overview

### Public API

- **`SVGDocument`**: Main class for SVG documents and resources
- **`convert()`**: Convenience function for simple conversions

### Internal Structure

**Converter Architecture** - Modular design with multiple inheritance:

- `Converter` (internal) inherits from: `AdjustmentConverter`, `EffectConverter`, `LayerConverter`, `PaintConverter`, `ShapeConverter`, `TextConverter`

**Key Modules**:

- `src/psd2svg/core/` - Internal converter implementations
- `src/psd2svg/svg_document.py` - Public API
- `src/psd2svg/rasterizer/` - Rasterization backends (resvg, playwright)

**Rasterizers**:

- `ResvgRasterizer` - Default, fast production rasterizer (resvg-py)
- `PlaywrightRasterizer` - Optional browser-based renderer (better SVG 2.0 support)

### Dependencies

- `psd-tools>=1.12.0` - PSD parsing
- `pillow` - Image processing
- `numpy` - Numerical operations
- `resvg-py` - SVG rasterization
- `fontconfig-py>=0.4.0` - Font resolution with CharSet support (Linux/macOS)
- `fonttools[woff]` - Font subsetting and WOFF/WOFF2 conversion

## Important Considerations

### SVG Features

**SVG 2.0 Usage**:

- Uses `transform-origin` for gradients (cleaner than nested transforms)
- Falls back to translate-rotate-translate for offset transforms
- Supported by modern browsers and resvg-py 0.28+

**Optimization** (enabled by default):

- Consolidates all `<defs>` elements into single global `<defs>`
- Can be disabled with `optimize=False` in `save()` or `tostring()`

### Text Layer Conversion

**Experimental feature** - Enabled by default:

- Converts text to native SVG `<text>` elements when fonts available
- Falls back to rasterization when fonts missing
- Requires `fontconfig` (Linux/macOS only)
- Disable with `enable_text=False`

**Known limitations**:

- Text wrapping in bounding boxes not fully supported
- Kerning and ligatures not supported
- Variable fonts may not render correctly with resvg-py (use PlaywrightRasterizer)

### Advanced Features

All these features are documented in detail at [psd2svg.readthedocs.io](https://psd2svg.readthedocs.io/):

- **Font embedding**: `embed_fonts=True` (increases file size)
- **Font subsetting**: `font_format='woff2'` (90%+ size reduction, requires `fonts` group)
- **Class attributes**: `enable_class=True` (debugging only, disabled by default)
- **Letter spacing**: `text_letter_spacing_offset` (compensation for renderer differences)
- **Text wrapping**: `text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT` (bounding box text)

### Known Issues

**resvg-py Variable Font Bug**:

- Does not correctly apply `font-weight` for variable fonts
- Workaround: Use PlaywrightRasterizer or static font variants
- Monitor upstream: <https://github.com/sparkfish/resvg-py>

**Thread Safety**:

- APIs are NOT thread-safe

**SVG Compatibility**:

- SVG 1.1 doesn't support all Photoshop blending modes (e.g., `linear-dodge`)
- Filter effects are approximations
- Most adjustment layers not implemented
- Smart object filters not supported

## Testing

### Font Requirements

Tests require specific fonts. Missing fonts cause tests to be skipped (not failed).

**Core fonts** (always installed in CI):

- MS Core Fonts (Arial, Times New Roman, etc.)
- Noto Sans, Noto Sans CJK

**Optional fonts** (tests auto-skip if unavailable):

- Noto Sans Arabic, Devanagari, Thai, Hebrew

**Local setup**:

```bash
# Ubuntu/Debian
sudo apt-get install fonts-noto-core fonts-noto-cjk fonts-noto-ui-core
sudo fc-cache -fv

# macOS
brew tap homebrew/cask-fonts
brew install --cask font-noto-sans font-noto-sans-cjk-jp
```

**Pytest markers**: `@requires_noto_sans_jp`, `@requires_noto_sans_cjk`, etc.

## CI/CD

### GitHub Actions

**Test Workflow** (`.github/workflows/test.yml`):

- Runs on every push and PR
- Tests Python 3.10, 3.11, 3.12, 3.13, 3.14
- Runs linting (ruff), type checking (mypy), tests (pytest)

**Release Workflow** (`.github/workflows/release.yml`):

- Triggered by version tags (`v*`)
- Builds and publishes to PyPI (OIDC)
- Creates GitHub releases

```bash
# To release:
git tag v0.3.0
git push origin v0.3.0
```

### Git Workflow

**IMPORTANT**: This project uses a pull request workflow for all changes to the main branch.

**Never commit directly to main.** All changes must:

1. Be developed on a feature branch
2. Be pushed to the remote repository
3. Go through a pull request targeting `main`
4. Pass CI checks before merging

**Workflow example:**

```bash
# Create feature branch
git checkout -b feature/my-change

# Make changes and commit
git add .
git commit -m "Description of changes"

# Push branch and create PR
git push -u origin feature/my-change
gh pr create --title "My Change" --body "Description"
```

## Code Quality Standards

- **Type hints**: Full type annotation coverage
- **Linting**: Ruff for fast linting/formatting
- **Python 3.10+**: Modern Python, no legacy code
- **Abstract base classes**: Proper ABC usage for interfaces
- **Import statements**: Prefer top-/module-level import over function-level import

## Development Notes

### When Making Changes

1. **Read files before modifying** - Understand existing patterns
2. **Avoid over-engineering** - Keep changes focused and minimal
3. **Security** - Watch for command injection, XSS, SQL injection
4. **Avoid backwards-compatibility hacks** - Delete unused code completely
5. **No time estimates** - Provide concrete steps, not timelines

### File Operations

Prefer specialized tools over bash:

- **Read** for reading files (not `cat`/`head`/`tail`)
- **Edit** for editing (not `sed`/`awk`)
- **Write** for creating files (not `echo >` or `cat <<EOF`)
- **Glob** for finding files (not `find`)
- **Grep** for searching content (not `grep`/`rg`)

### Documentation Structure

- **README.md** - Quick start guide, basic usage
- **CLAUDE.md** (this file) - Development guidance for Claude Code
- **docs/** - Full Sphinx documentation (comprehensive details)

For detailed feature documentation, configuration options, and usage examples, refer to the [full documentation](https://psd2svg.readthedocs.io/).

### Debugging PSD files

Use `psd-tools` API to inspect PSD content. For text layers, use the following approach:

```python
from psd_tools import PSDImage
from psd_tools.api.layers import TypeLayer
from psd2svg.core.text import TypeSetting

psdimage = PSDImage.open("tests/fixtures/texts/style-tsume.psd")
for layer in psd.descendants():
   if isinstance(layer, TypeLayer) and layer.is_visible():
      text_setting = TypeSetting(layer._data)
      for paragraph in text_setting:
         for style in paragraph:
            # Do whatever you want to debug with the style span.
            pass
```
