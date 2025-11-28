Changelog
=========

This document tracks changes across versions of psd2svg.

Version 0.3.0 (In Development)
------------------------------

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
