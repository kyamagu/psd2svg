Changelog
=========

This document tracks changes across versions of psd2svg.

Version 0.6.0
-------------

**Added:**

* Support for kerning in text layers using dx/dy attributes
* Support for tsume (East Asian character tightening) in text layers
* Support for ligatures (common and discretionary) via font-variant-ligatures CSS property
* New ``SVGDocument.append_css()`` API for custom CSS injection
* SVG optimization: merge consecutive sibling tspan elements with identical attributes (41% size reduction)

**Fixed:**

* Fixed ``merge_singleton_children()`` losing nested elements during optimization
* Fixed ``merge_attribute_less_children()`` losing nested elements during optimization
* Fixed character extraction to include element tail text for accurate font subsetting

**Changed:**

* Refactored font-related SVG utilities to ``svg_utils`` module for better code organization
* Enhanced merge functions to unwrap redundant wrapper elements for cleaner SVG output
* Improved SVG structure optimization with better handling of nested elements

Version 0.5.0
-------------

**Added:**

* Windows font resolution support via Windows registry
* Cross-platform font mapping with 572 common fonts (no external dependencies required)
* Hybrid font resolution system (static mapping + platform-specific fallback)
* Automatic font fallback chain generation for embedded fonts

**Changed:**

* Refactored font module imports for cleaner code organization
* Improved documentation for Windows font resolution and cross-platform support
* Enhanced documentation for adjustment layer transparency limitations

**Removed:**

* Redundant ``SVGDocument.optimize()`` method (use ``optimize`` parameter in ``save()``/``tostring()`` instead)

Version 0.4.0
-------------

**Added:**

* Text wrapping support with foreignObject for bounding box text
* Font embedding support with configurable formats (TTF, OTF, WOFF, WOFF2)
* SVG optimization with ``consolidate_defs()`` function (enabled by default)
* ``enable_class`` flag to control class attribute insertion (disabled by default)
* PlaywrightRasterizer support for Windows platform
* Text letter-spacing configuration option for renderer-specific adjustments

**Fixed:**

* Context management for element creation using consistent ``set_current()`` pattern
* Blend subtraction constant in ``BLEND_MODE`` and ``INACCURATE_BLEND_MODES``
* PlaywrightRasterizer to work in asyncio event loops (Jupyter notebooks)
* Omit no-op ``translate(0,0)`` in gradient transforms

**Changed:**

* ``enable_title`` default changed from ``True`` to ``False`` for cleaner output
* Refactored gradient transforms to use SVG 2.0 ``transform-origin`` attribute
* Refactored image handling from list-based to ID-based mapping
* Improved font embedding implementation for better maintainability
* Documentation improvements: reorganized user guide, fixed inaccuracies, added examples

Version 0.3.0
-------------

**Added:**

* Font subsetting support with pyftsubset for web optimization

  * Reduces embedded font file sizes by 90%+ (150KB → 10KB typical)
  * Support for TTF, OTF, and WOFF2 output formats
  * Automatic character extraction from SVG text elements
  * Optional dependency group: ``pip install psd2svg[fonts]``
  * New parameters: ``subset_fonts`` and ``font_format`` in ``SVGDocument.save()`` and ``tostring()``
  * WOFF2 format automatically enables subsetting for best compression
  * New module: ``psd2svg.font_subsetting`` with ``extract_used_unicode()`` and ``subset_font()``

* SVGDocument API for more control over conversions
* Export and load functionality
* Comprehensive Sphinx documentation
* Pattern fill and stroke support for shapes
* Paint converter split from shape converter

**Fixed:**

* Transform handling with clip-path and mask
* Various rendering improvements

**Changed:**

* Improved API design with SVGDocument class
* Refactored paint methods into separate PaintConverter

Version 0.2.0
-------------

**Added:**

* Rasterization support with multiple backends
* Support for external image resources
* Resource path handling in CLI

**Changed:**

* Better image handling (embedded vs external)
* Enhanced command-line interface

Version 0.1.x
-------------

**Added:**

* Initial release
* Basic PSD to SVG conversion
* Command-line tool
* Simple Python API
* Layer and shape support
* Basic effects support

Previous Versions
-----------------

For historical changes, see the git commit history at:
https://github.com/kyamagu/psd2svg/commits/main
