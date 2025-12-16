# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Clipping mask and layer mask combination rendering**
  - Fixed browser compatibility issue when both clipping mask and layer mask exist on the same layer
  - Previous approach using nested mask references (`<mask mask="url(#id)">`) doesn't work reliably across browsers
  - Now transfers mask/clip-path attributes to mask content elements for proper composition hierarchy
  - Improved test quality thresholds for clipping-4 test cases (from 0.005 to 0.001 MSE)
  - Added test fixture `clipping-5-mask-with-effect.psd` to validate the fix

## [0.9.0] - 2025-12-15

### Added

- **Experimental arc warp support for text layers** (#164)
  - Implements `TextPathData.ArcWarp` conversion to SVG `<textPath>` with arc
  - Supports horizontal/vertical arc orientation with upper/lower placement
  - Comprehensive unit tests for arc warping feature
  - Enables rendering of text along curved paths from PSD files

- **SVG optimization features** (#163, #168)
  - Definition deduplication: Consolidates duplicate gradient/pattern/filter definitions
  - Unwrap attribute-less `<g>` elements to reduce SVG nesting and file size
  - Improves SVG output quality and reduces redundancy

- **Japanese font mappings** (#167)
  - Added comprehensive Japanese font mappings from Screen website
  - Improves font resolution for Japanese typography

- **Conditional whitespace preservation** (#159)
  - Intelligently preserves whitespace only when necessary for text layers
  - Reduces unnecessary `xml:space="preserve"` attributes

### Fixed

- **Font attribute redundancy** (#170)
  - Fixed redundant `font-weight` and `font-style` attributes on inherited elements
  - Reduces SVG file size and improves output cleanliness

- **Font-family quote handling** (#166)
  - Fixed redundant quotes in `font-family` attributes
  - Ensures proper CSS formatting

- **Hiragino font PostScript names** (#171)
  - Fixed double-W suffix bug in Hiragino font PostScript name generation
  - Improves font matching accuracy for Hiragino font family

- **Text property conversions** (#161, #165)
  - Fixed tsume property scaling for accurate letter-spacing calculation
  - Refactored text scaling to use `font-size` for uniform scaling instead of transform
  - Extracted font scaling logic into helper method for better maintainability

### Changed

- **SVG output improvements** (#172, #174)
  - Wrap mask and clipPath elements in `<defs>` containers for better SVG structure
  - Use `fill="none"` instead of `fill="transparent"` for cleaner SVG output

- **Font mapping refactoring** (#171)
  - Refactored Hiragino font mapping to use declarative structure
  - Improves maintainability and extensibility of font mappings

- **Logging improvements** (#173)
  - Adjusted font resolution logging levels to reduce verbosity
  - Less noisy output during normal operations

- **Browser compatibility warnings** (#160)
  - Added warning about text scaling not being supported by browsers
  - Helps users understand rendering limitations

### Internal

- **Code organization** (#162)
  - Split text module into separate `text` and `typesetting` modules
  - Improves code structure and maintainability

- **Documentation** (#169)
  - Enhanced `consolidate_defs` documentation for mask exclusion behavior
  - Updated arc warp support documentation

### Testing

- All 770 tests passing
- Added comprehensive unit tests for arc warping feature
- Added tests for SVG optimization features

## [0.8.0] - 2025-12-10

### Added

- **Font weight and style inference from PostScript name suffixes** (#156)
  - Automatically infers font weight and style from PostScript name suffixes (e.g., "-Bold", "-Italic", "Mt", "Rg")
  - Supports abbreviated suffixes: Bd, Md, Lt, Rg, It, Obl, Cn, Ex
  - Supports medium-length suffixes: Bold, Demi, Book, Black, Thin, Heavy, Ital, Oblique, Narrow, Extended
  - Supports Japanese font weight notation: W0-W9 (e.g., "NotoSansJP-W7" → weight 700)
  - Case-insensitive suffix parsing for better compatibility
  - Improves font matching accuracy when exact PostScript names aren't found

### Fixed

- **Font resolution with variation selectors and combining marks** (#157)
  - Fixed charset-based font matching to properly handle Unicode variation selectors (U+FE00-FE0F, U+E0100-E01EF)
  - Fixed handling of combining diacritical marks (U+0300-U+036F, U+1AB0-U+1AFF, U+1DC0-U+1DFF, U+20D0-U+20FF, U+FE20-FE2F)
  - Filters these special characters before querying font charset to prevent matching failures
  - Resolves issues with CJK text containing variation selectors and accented characters
  - Control characters (C0: 0-31, DEL: 127, C1: 128-159) now properly filtered

### Changed

- **Refactored font resolution architecture** (#145, #148, #149)
  - Split `FontInfo.find()` into two explicit methods:
    - `FontInfo.lookup_static()`: Fast lookup using static mapping (no platform queries)
    - `FontInfo.resolve()`: Full resolution with platform-specific queries and file paths
  - `FontInfo.find()` now delegates to `lookup_static()` by default (backward compatible)
  - Eliminated redundant font resolution in `embed_fonts=True` flow
  - Font subsetting now uses `set[int]` for codepoints instead of `set[str]`
  - Made `resolved_fonts_map` parameter required in `_insert_css_fontface()`
  - Improved performance and code clarity throughout font resolution pipeline

- **Charset-based font matching improvements** (#144)
  - Added charset matching to `FontInfo.find()` API
  - Empty charset codepoints now handled as `None` in font matching
  - Refactored `create_charset_codepoints()` to never return `None`

### Internal

- **Documentation improvements**
  - Complete rewrite of Font Resolution Strategy section in CLAUDE.md
  - Added detailed explanation of deferred resolution architecture
  - Documented distinction between `lookup_static()` and `resolve()` methods
  - Added charset-based font matching documentation
  - Updated release workflow to require pull requests for all changes

- **Code quality**
  - Refactored internal helpers for naming consistency
  - Extracted custom mapping validation in `FontInfo.resolve()`
  - Removed unused `FontInfo.resolve()` method (old implementation)
  - Added docstring notes about CSS 'font' shorthand property
  - Refactored and added tests for `add_font_family()` function

### Testing

- All 666 tests passing (15 skipped, 15 xfailed)
- Added comprehensive tests for font weight suffix parsing
- Added tests for variation selector and combining mark handling
- Updated font resolution tests for new API structure

## [0.7.1] - 2025-12-09

### Fixed

- Control character filtering in charset-based font matching
- Fontconfig API usage in charset-based font resolution

## [0.7.0] - 2025-12-08

### Added

- **Unicode codepoint-based font matching** (#135)
  - Intelligent font matching that analyzes which Unicode characters are actually used in text layers
  - Character extraction and codepoint conversion for better glyph coverage detection
  - Automatic fallback to name-only matching on errors
  - Platform-specific implementation:
    - Linux/macOS: Uses fontconfig CharSet API for native charset querying
    - Windows: Uses fontTools cmap table checking (requires 80%+ coverage by default)
  - Significantly improves font selection for multilingual text (CJK, Arabic, Devanagari, etc.)
  - Reduces font substitution warnings
  - Minimal performance overhead (~10-50ms per document)

- **file:// URL support for PlaywrightRasterizer fonts** (#136)
  - Added `create_file_url()` utility for cross-platform file:// URL generation
  - New `_insert_css_fontface_file_urls()` method for local font references
  - Performance improvements when using PlaywrightRasterizer:
    - 60-80% faster rasterization (no font encoding/subsetting overhead)
    - 99% smaller SVG strings (no base64 encoding)
    - More robust error handling
    - Lower memory usage
  - Automatically used by `rasterize()` when PlaywrightRasterizer is detected
  - Transparent to users - no API changes required

### Changed

- **Refactored font embedding architecture** (#136)
  - Renamed `_embed_fonts()` → `_insert_css_fontface_data_uris()` for clarity
  - Split font CSS insertion into two modes: data URI encoding vs file:// URLs
  - Character extraction logic now shared between charset matching and font subsetting

- **Improved API design** (#137)
  - Moved `copy.deepcopy()` from `SVGDocument._handle_images()` to public methods `tostring()` and `save()`
  - Makes immutability guarantees explicit at the public API level
  - Updated `_handle_images()` to accept `svg: ET.Element` parameter and document in-place modification
  - Aligns with existing `_insert_css_fontface()` pattern
  - No behavioral changes - maintains backward compatibility

### Internal

- **Code quality improvements** (#138)
  - Moved function-level imports to module-level across test files
  - Follows Python best practices for import organization
  - Affected modules: `test_enable_class.py`, `test_text.py`, `test_playwright_rasterizer.py`,
    `test_resvg_rasterizer.py`, `test_generate_font_mapping.py`, `test_svg_document.py`, `test_font_mapping.py`
  - Intentionally preserved try-except blocks for optional dependency imports

### Testing

- Added 5 new unit tests for `create_file_url()` covering cross-platform scenarios
- Added 2 new integration tests for PlaywrightRasterizer with file:// URLs
- Updated existing tests to reflect new font embedding behavior
- All 588 tests passing

## [0.6.0] - 2024-XX-XX

Previous releases - see git history for details.

[0.9.0]: https://github.com/kyamagu/psd2svg/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/kyamagu/psd2svg/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/kyamagu/psd2svg/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/kyamagu/psd2svg/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/kyamagu/psd2svg/releases/tag/v0.6.0
