# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.10.0] - 2025-12-17

### Added

- **Comprehensive adjustment layer support** (#189, #191, #192, #194, #196, #198, #203, #204)
  - Posterize adjustment layer support
  - HueSaturation adjustment layer support
  - Exposure adjustment layer support
  - BrightnessContrast adjustment layer support
  - Threshold adjustment layer support
  - ColorBalance adjustment layer support with accuracy warnings
  - Curves adjustment layer support
  - Levels adjustment layer support
- **Morisawa font mappings** (#180)
  - Added 4,042 Morisawa fonts for enhanced Japanese typography support
  - Migrated font mappings to JSON resource files with lazy loading
  - Total static mapping: 539 default + 370 Hiragino + 4,042 Morisawa fonts

### Fixed

- **Clipping mask and layer mask rendering** (#178)
  - Fixed browser compatibility when both masks exist on same layer
  - Transfers mask attributes to content elements instead of nested mask references
- **Font weight consistency** (#183)
  - Use numeric "700" instead of "bold" for consistent CSS output (#179)
- **Browser optional dependency** (#177)
  - Fixed browser dependency group configuration
- **Documentation updates** (#186, #187, #197)
  - Fixed 'browser group' references to 'browser extra' throughout docs
  - Fixed multiple outdated references in development.rst
  - Updated adjustment layer documentation for clarity
- **Font logging** (#184)
  - Added quotes around file paths in log messages

### Changed

- **Font mapping architecture** (#180)
  - Consolidated duplicate font loading logic
  - Corrected Hiragino W1-W3 weight mappings
  - Resolution order: Custom → Default → Hiragino → Morisawa
- **Adjustment layer architecture** (#200, #201)
  - Refactored adjustment layer methods with stubs for unimplemented types
  - Refactored `AdjustmentConverter._create_filter` to use svg_utils helpers

### Internal

- Documentation improvements (#182, #190, #193, #202)
  - Streamlined CLAUDE.md and improved documentation structure
  - Added PSD file debugging tips and low-level inspection examples
  - Added `uv run python` command to quick reference
  - Consolidated changelog to use CHANGELOG.md as single source
- Refactored lightness adjustment into shared helper method (#191)
- Updated release workflow to include `uv sync` and `uv.lock` (#176)
- Updated uv.lock for v0.9.0 (#176)

## [0.9.0] - 2025-12-15

### Added

- **Arc warp support for text layers** (#164)
  - Converts `TextPathData.ArcWarp` to SVG `<textPath>` with arc
  - Supports horizontal/vertical orientation with upper/lower placement
- **SVG optimization** (#163, #168)
  - Definition deduplication for gradients/patterns/filters
  - Unwrap attribute-less `<g>` elements to reduce nesting
- **Japanese font mappings** (#167)
  - Added comprehensive mappings from Screen website
- **Conditional whitespace preservation** (#159)
  - Only preserves whitespace when necessary for text layers

### Fixed

- **Font attribute redundancy** (#170)
  - Fixed redundant `font-weight` and `font-style` on inherited elements
- **Font-family quote handling** (#166)
  - Fixed redundant quotes in `font-family` attributes
- **Hiragino font PostScript names** (#171)
  - Fixed double-W suffix bug in PostScript name generation
- **Text property conversions** (#161, #165)
  - Fixed tsume property scaling for letter-spacing
  - Refactored text scaling to use `font-size` instead of transform

### Changed

- **SVG output** (#172, #174)
  - Wrap mask/clipPath elements in `<defs>` containers
  - Use `fill="none"` instead of `fill="transparent"`
- **Font mapping** (#171)
  - Refactored Hiragino mapping to declarative structure
- **Logging** (#173)
  - Reduced font resolution verbosity
- **Browser warnings** (#160)
  - Added warning about text scaling browser limitations

### Internal

- Split text module into `text` and `typesetting` modules (#162)
- Enhanced documentation for `consolidate_defs` and arc warp (#169)

## [0.8.0] - 2025-12-10

### Added

- **Font weight/style inference from PostScript suffixes** (#156)
  - Auto-infers weight and style from suffixes (e.g., "-Bold", "-Italic", "Mt", "Rg")
  - Supports abbreviated, medium-length, and Japanese W0-W9 notation
  - Case-insensitive parsing

### Fixed

- **Font resolution with Unicode special characters** (#157)
  - Fixed charset matching for variation selectors and combining marks
  - Filters control characters before font charset queries

### Changed

- **Font resolution architecture** (#145, #148, #149)
  - Split `FontInfo.find()` into `lookup_static()` and `resolve()` methods
  - Eliminated redundant resolution in `embed_fonts=True` flow
  - Font subsetting uses `set[int]` for codepoints
- **Charset-based font matching** (#144)
  - Added charset matching to `FontInfo.find()` API
  - Empty charset codepoints handled as `None`

### Internal

- Font Resolution Strategy documentation rewrite in CLAUDE.md
- Refactored internal helpers and validation
- Updated release workflow for PR requirements

## [0.7.1] - 2025-12-09

### Fixed

- Control character filtering in charset-based font matching
- Fontconfig API usage in charset-based font resolution

## [0.7.0] - 2025-12-08

### Added

- **Unicode codepoint-based font matching** (#135)
  - Analyzes actual Unicode characters used in text layers for better font selection
  - Platform-specific: fontconfig CharSet API (Linux/macOS), fontTools cmap (Windows)
  - Improves multilingual text support (CJK, Arabic, Devanagari, etc.)
  - Minimal overhead (~10-50ms per document)
- **file:// URL support for PlaywrightRasterizer** (#136)
  - 60-80% faster rasterization with local font references
  - 99% smaller SVG strings (no base64 encoding)
  - Automatic when PlaywrightRasterizer detected

### Changed

- **Font embedding architecture** (#136)
  - Renamed `_embed_fonts()` → `_insert_css_fontface_data_uris()`
  - Split into data URI vs file:// URL modes
  - Shared character extraction for charset matching and subsetting
- **API design** (#137)
  - Moved `copy.deepcopy()` to public methods for explicit immutability

### Internal

- Moved function-level imports to module-level in test files (#138)

## [0.6.0] - 2024-XX-XX

Previous releases - see git history for details.

[0.10.0]: https://github.com/kyamagu/psd2svg/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/kyamagu/psd2svg/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/kyamagu/psd2svg/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/kyamagu/psd2svg/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/kyamagu/psd2svg/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/kyamagu/psd2svg/releases/tag/v0.6.0
