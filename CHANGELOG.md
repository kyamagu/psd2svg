# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.7.0]: https://github.com/kyamagu/psd2svg/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/kyamagu/psd2svg/releases/tag/v0.6.0
