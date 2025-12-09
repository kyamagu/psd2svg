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

psd2svg uses a sophisticated multi-tiered approach to resolve fonts with intelligent charset-based matching:

#### 1. Resolution Tiers

**Tier 1 - Static mapping (primary)**: 572 common fonts mapped by PostScript name

- Cross-platform compatibility
- No external dependencies
- Works on Windows, Linux, macOS
- Enables text conversion everywhere

**Tier 2 - Platform-specific resolution (fallback)**: Query system fonts when needed

- **Linux/macOS**: fontconfig with CharSet API (requires fontconfig-py >= 0.4.0)
- **Windows**: Windows registry + fontTools parsing with cmap table checking
- Font file path discovery enables font embedding
- Automatically invoked by `FontInfo.resolve()` when resolving fonts

**Resolution priority**: Custom mapping (via `font_mapping` parameter) → Static mapping → Platform-specific

**Custom font mapping**: Users can provide custom mappings via `font_mapping` parameter for fonts not in default mapping. See CLI tool: `python -m psd2svg.tools.generate_font_mapping`

#### 2. Unicode Codepoint-Based Matching

**Feature**: Charset-aware font matching (implemented in feature/charset-font-matching)

psd2svg performs intelligent font matching by analyzing which Unicode characters are actually used in the text:

**How it works**:

1. **Character extraction**: Extracts all Unicode characters from text layers
2. **Codepoint conversion**: Converts characters to numeric codepoints (e.g., 'あ' → 0x3042)
3. **Smart resolution**: Prioritizes fonts with better glyph coverage for those specific characters
4. **Automatic fallback**: Gracefully falls back to name-only matching on any errors

**Platform implementation**:

- **Linux/macOS**: Uses fontconfig CharSet API for native charset querying
- **Windows**: Uses fontTools cmap table checking (requires 80%+ coverage by default)
- **Automatic**: Always enabled, no configuration needed, graceful degradation

**Benefits**:

- Better font selection for multilingual text (CJK, Arabic, Devanagari, etc.)
- Reduces font substitution warnings
- Finds fonts with actual glyph support vs. just name matching
- Minimal performance overhead (~10-50ms per document)
- Character extraction reused for both charset matching and font subsetting

#### 3. Automatic Font Fallback Chains

When fonts are embedded, psd2svg automatically:

1. Resolves requested fonts to actual system fonts via `FontInfo.resolve()`
2. Detects font substitutions (e.g., Arial → DejaVu Sans)
3. Generates CSS fallback chains: `font-family: 'Arial', 'DejaVu Sans'`
4. Embeds the actual substitute font in @font-face rules
5. Updates SVG text elements with fallback chains

This ensures correct rendering when requested fonts are unavailable. Font substitutions are logged at INFO level, charset matching at DEBUG level.

#### 4. Font CSS Insertion Architecture

**Unified implementation** with boolean flag for encoding mode:

```text
_insert_css_fontface(svg, subset_fonts, font_format, use_data_uri)
  │
  ├─ _collect_resolved_fonts(svg)
  │   └─ Returns: list[(FontInfo, set[str])] (deduplicated by font path)
  │
  ├─ _generate_css_rules_for_fonts()
  │   └─ if use_data_uri: encode_font_with_options() (with subsetting)
  │   └─ else: create_file_url() (no subsetting)
  │
  └─ insert_or_update_style_element() - Insert CSS into SVG
```

**Usage modes:**

- `tostring()`/`save()`: use_data_uri=True (portable SVG files)
- `rasterize()` with PlaywrightRasterizer: use_data_uri=False (60-80% faster, file:// URLs)

#### 5. Font Resolution Patterns

**Deferred Resolution Architecture** (current implementation):

psd2svg uses a deferred font resolution approach that preserves original PostScript names from PSD files:

```python
# During PSD → SVG conversion:
# - PostScript names stored directly in font-family attributes
# - No font resolution performed (fast conversion)
# - Original PSD intent preserved perfectly

# During output (save/tostring/rasterize):
# - Extract PostScript names from SVG tree
# - Resolve PostScript → family names with charset-based matching
# - Update font-family attributes with resolved names + fallbacks
# - Embed fonts if requested
```

**Benefits**:

- **Faster conversion**: No font resolution during PSD parsing
- **Better accuracy**: Original PostScript names preserved until output
- **Better matching**: Charset-based resolution with actual text content
- **No information loss**: Failed resolution doesn't lose PostScript names

**Font resolution flow**:

1. **Conversion time**: `TypeSetting.get_postscript_name(font_index)` extracts PostScript names from PSD font set
2. **Output time**: `_resolve_postscript_to_family(ps_name, charset_codepoints)` resolves to family names
3. **Font embedding**: Only performed when `embed_fonts=True` or using PlaywrightRasterizer

**Two-step resolution pattern** (used internally):

```python
# Step 1: Find font metadata (static mapping for 572 common fonts)
font = FontInfo.find('ArialMT')
# Returns immediately if in static mapping, with family/style/weight but no file path

# Step 2: Resolve to system font file with charset matching (when needed for embedding)
codepoints = {0x3042, 0x3044}  # Japanese hiragana
resolved = font.resolve(charset_codepoints=codepoints)
# Queries system with charset-based matching to find font file
```

**Key architectural points**:

- `TypeSetting.get_postscript_name()`: Extract PostScript name from PSD (no resolution)
- `FontInfo.find()`: Metadata lookup with optional charset-based fallback (Tier 3 only)
- `FontInfo.resolve()`: System font file resolution with charset matching (always queries system)
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
