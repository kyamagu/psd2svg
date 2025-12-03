Font Handling
=============

This guide covers font embedding, subsetting, and optimization for SVG output.

Overview
--------

psd2svg can embed fonts directly in SVG files using ``@font-face`` CSS rules. For web delivery, font subsetting dramatically reduces file sizes by including only the glyphs actually used.

**Installation:**

Font subsetting requires the ``fonts`` optional dependency group:

.. code-block:: bash

   pip install psd2svg[fonts]

This installs ``fontTools`` and other required packages for font manipulation.

Font Embedding Basics
----------------------

Simple Embedding
~~~~~~~~~~~~~~~~

Embed fonts as base64-encoded data URIs in the SVG:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, embed_fonts=True)
   document.save("output.svg")

**Result:** Fonts are embedded as base64-encoded TTF/OTF files in ``@font-face`` rules.

**Pros:**

* Self-contained SVG files (no external font dependencies)
* Consistent rendering across platforms
* Works offline

**Cons:**

* Much larger file sizes (100KB+ per font)
* Base64 encoding adds ~33% overhead
* May include glyphs not used in the document

Font Subsetting (Recommended)
------------------------------

What is Font Subsetting?
~~~~~~~~~~~~~~~~~~~~~~~~~

Font subsetting creates minimal font files containing only the glyphs actually used in your SVG. This typically reduces font file sizes by 90-95%.

**Example:** If your SVG only uses "Hello World", the subset font will only contain the glyphs for H, e, l, o, W, r, d (plus space and punctuation).

Using WOFF2 Format
~~~~~~~~~~~~~~~~~~

WOFF2 provides the best compression and automatically enables subsetting:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, embed_fonts=True)

   # Save with WOFF2 subsetting
   document.save("output.svg", font_format="woff2")

**Result:** Fonts are:

1. Analyzed to extract used glyphs
2. Subset to include only those glyphs
3. Compressed with WOFF2 (best compression)
4. Embedded as base64 data URIs

**Typical Size Reduction:**

* Original TTF: 150 KB
* Subset WOFF2: 5-10 KB (90-95% reduction)

Supported Font Formats
~~~~~~~~~~~~~~~~~~~~~~

The ``font_format`` parameter accepts:

* ``woff2`` - Best compression, subset automatically (recommended)
* ``woff`` - Good compression, subset automatically
* ``ttf`` - No compression, subset if glyphs specified
* ``otf`` - No compression, subset if glyphs specified

.. code-block:: python

   # WOFF2 (recommended)
   document.save("output.svg", font_format="woff2")

   # WOFF (good compression)
   document.save("output.svg", font_format="woff")

   # TTF (no compression, larger files)
   document.save("output.svg", font_format="ttf")

Advanced Subsetting Options
----------------------------

Manual Glyph Selection
~~~~~~~~~~~~~~~~~~~~~~

For advanced use cases, you can manually specify glyphs to include:

.. code-block:: python

   from psd2svg.font_subsetting import extract_used_unicode, subset_font
   import xml.etree.ElementTree as ET

   # Parse SVG
   svg_tree = ET.parse("output.svg").getroot()

   # Extract Unicode characters per font
   font_usage = extract_used_unicode(svg_tree)
   # => {"Arial": {"H", "e", "l", "o"}, "Times": {"W", "r", "d"}}

   # Subset a font file
   font_bytes = subset_font(
       input_path="/usr/share/fonts/arial.ttf",
       output_format="woff2",
       unicode_chars={"H", "e", "l", "o"}
   )
   # => b'wOF2...' (WOFF2 font bytes)

**Note:** This is typically used internally by ``SVGDocument.save()`` and ``tostring()`` methods. Direct usage is only needed for custom workflows.

Subsetting with tostring()
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Font subsetting also works with the ``tostring()`` method:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, embed_fonts=True)

   # Get SVG string with WOFF2 subsetting
   svg_string = document.tostring(font_format="woff2")

Browser Compatibility
---------------------

Font Format Support
~~~~~~~~~~~~~~~~~~~

Modern browsers have excellent font format support:

* **WOFF2**: Chrome 36+, Firefox 39+, Safari 10+, Edge 14+ (recommended)
* **WOFF**: Chrome 5+, Firefox 3.6+, Safari 5.1+, Edge 12+
* **TTF/OTF**: Universal support (but larger files)

For maximum compatibility with older browsers, use WOFF:

.. code-block:: python

   document.save("output.svg", font_format="woff")

Font Loading Behavior
~~~~~~~~~~~~~~~~~~~~~~

Embedded fonts in SVG are loaded immediately when the SVG is parsed. There is no FOUT (Flash of Unstyled Text) or layout shift.

Font Licensing
--------------

Important Considerations
~~~~~~~~~~~~~~~~~~~~~~~~

Font embedding and subsetting may be subject to licensing restrictions. Before distributing SVG files with embedded fonts:

1. **Check font licenses** - Verify the font license allows embedding
2. **Review restrictions** - Some licenses prohibit subsetting or modification
3. **Commercial fonts** - May require additional licensing for web use
4. **Open source fonts** - Generally more permissive (e.g., SIL OFL, Apache)

**Note:** Font subsetting creates a derivative work. Ensure your font license permits this.

Consult with legal counsel if uncertain about font license compliance.

Troubleshooting
---------------

Subsetting Not Working
~~~~~~~~~~~~~~~~~~~~~~

If font subsetting isn't working:

1. **Check installation:**

   .. code-block:: bash

      pip install psd2svg[fonts]

2. **Verify fontTools is installed:**

   .. code-block:: python

      import fontTools
      print(fontTools.__version__)

3. **Check for errors** in the console output

Missing Glyphs
~~~~~~~~~~~~~~

If characters are missing after subsetting:

* The font may not contain glyphs for those characters
* Unicode normalization issues (e.g., composed vs decomposed characters)
* Try using ``font_format="ttf"`` without subsetting to verify

File Size Still Large
~~~~~~~~~~~~~~~~~~~~~

If file sizes are still large after subsetting:

* Multiple fonts may be embedded (each font adds size)
* Font may have extensive hinting data
* Try WOFF2 for best compression
* Consider using external font files instead of embedding

Performance Tips
----------------

Best Practices
~~~~~~~~~~~~~~

1. **Use WOFF2 for web** - Best compression and broad browser support
2. **Subset by default** - No reason not to with WOFF2
3. **Cache font files** - If using external fonts, leverage HTTP caching
4. **Limit font families** - Each font adds to file size
5. **Consider system fonts** - For non-critical text, use web-safe fonts

Comparison: Embedded vs External
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Embedded fonts (with subsetting):**

* **Pros:** Self-contained, no HTTP requests, works offline
* **Cons:** Larger initial file size (5-10KB per font)
* **Best for:** Single-page documents, offline use, email

**External fonts:**

* **Pros:** Smaller SVG files, fonts can be cached and reused
* **Cons:** Additional HTTP requests, requires server/CDN
* **Best for:** Multiple SVGs sharing fonts, web applications

Example: Optimized Web Delivery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, embed_fonts=True)

   # Optimize for web: WOFF2 subsetting, external images
   document.save(
       "output.svg",
       font_format="woff2",
       image_prefix="images/img",
       image_format="webp",
       enable_title=False  # Remove layer names
   )

This produces the smallest possible file while maintaining visual fidelity.
