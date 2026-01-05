# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **resvg-py upgrade** (#XXX)
  - Updated resvg-py from 0.2.3 to 0.2.5 for improved stability
  - Malformed/invalid SVG files now raise `ValueError` instead of crashing (SIGABRT)
  - Missing files now raise `ValueError` with proper error messages
  - Added error handling to ResvgRasterizer for better error reporting

### Fixed

- **Rasterizer stability** (#XXX)
  - Fixed process crashes when rasterizing malformed or empty SVG content
  - Added 4 new edge case tests for error handling validation
  - Removed crash warnings from documentation (Issue #242)

## [0.10.1] - 2025-12-19

### Security

- **CVE-2025-66034 fix** (#243)
  - Updated fonttools to 4.61.1 to address security vulnerability
- **Security improvements** (#224, #206)
  - Fixed multiple security issues (#219-223)
  - Fixed CodeQL alert for overly permissive regex range

### Added

- **ResourceLimits integration** (#231)
  - Complete DoS prevention with resource limits (Issue #221)

### Fixed

- **Gradient and effect rendering** (#211)
  - Fixed gradient color format issues
  - Fixed inner glow crashes (#209, #210)
- **Font handling** (#183, #184)
  - Fixed inconsistent font-weight values (Issue #179)
  - Added quotes around file paths in font resolution logs
- **Build and dependencies** (#207)
  - Updated uv.lock to version 0.10.0

### Changed

- **Error messages** (#241)
  - Improved resource limit error messages with actionable guidance
- **Code quality** (#213, #214, #215, #217, #218)
  - Fixed code quality violations (E501, PLC0415)
  - Converted relative imports to absolute imports in test files
  - Fixed font subsetting tests to use platform font resolution
  - Deprecated FontInfo.find() and removed unused has_postscript_font()
  - Removed unnecessary mypy overrides
- **Project structure** (#232, #208)
  - Removed unnecessary scripts directory
  - Updated copyright to CyberAgent, Inc.

### Documentation

- **Font resolution documentation** (#234)
  - Fixed font resolution documentation
  - Improved features/limitations documentation
- **Security documentation** (#233)
  - Refactored SECURITY.md to eliminate redundancy with docs/security.rst

### Internal

- **CI/CD updates**
  - Updated GitHub Actions dependencies (#225-229)
  - Bumped astral-sh/setup-uv from 3 to 7
  - Bumped actions/checkout from 4 to 6
  - Bumped github/codeql-action from 3 to 4
  - Bumped actions/upload-artifact from 4 to 6
  - Bumped actions/setup-python from 5 to 6

## [0.10.0] - 2025-12-17

### Added

- **Adjustment layer support** (#189, #191, #192, #194, #196, #198, #203, #204)
  - Posterize, HueSaturation, Exposure, BrightnessContrast, Threshold, ColorBalance, Curves, Levels
- **Morisawa font mappings** (#180)
  - 4,042 Morisawa fonts for Japanese typography
  - JSON resource files with lazy loading
  - Total: 539 default + 370 Hiragino + 4,042 Morisawa fonts

### Fixed

- **Clipping mask and layer mask combination** (#178)
  - Browser compatibility when both masks exist on same layer
- **Font weight values** (#183)
  - Use numeric "700" instead of "bold" for consistency
- **Browser optional dependency** (#177)
- **Documentation references** (#186, #187, #197)

### Changed

- **Font mapping architecture** (#180)
  - Corrected Hiragino W1-W3 weight mappings
  - Resolution order: Custom → Default → Hiragino → Morisawa
- **Adjustment layer refactoring** (#200, #201)

### Internal

- Documentation improvements and debugging tips (#182, #190, #193, #202)
- Updated release workflow (#176)

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

[0.10.1]: https://github.com/kyamagu/psd2svg/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/kyamagu/psd2svg/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/kyamagu/psd2svg/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/kyamagu/psd2svg/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/kyamagu/psd2svg/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/kyamagu/psd2svg/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/kyamagu/psd2svg/releases/tag/v0.6.0
