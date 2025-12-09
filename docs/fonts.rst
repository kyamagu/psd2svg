Font Handling
=============

This guide covers font embedding, subsetting, and optimization for SVG output.

Overview
--------

psd2svg can embed fonts directly in SVG files using ``@font-face`` CSS rules. For web delivery, font subsetting dramatically reduces file sizes by including only the glyphs actually used.

**Note:** Font subsetting is enabled by default when embedding fonts. The required ``fonttools`` package is automatically installed with psd2svg.

**Platform Support:**

* **Linux/macOS**: Full font resolution and embedding via fontconfig
* **Windows**: Full font resolution and embedding via Windows registry + fontTools parsing

Font Embedding Basics
----------------------

Simple Embedding
~~~~~~~~~~~~~~~~

Embed fonts as base64-encoded data URIs in the SVG:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)
   document.save("output.svg", embed_fonts=True)

**Result:** Fonts are embedded as base64-encoded TTF/OTF files in ``@font-face`` rules.

**Pros:**

* Self-contained SVG files (no external font dependencies)
* Consistent rendering across platforms
* Works offline

**Cons:**

* Much larger file sizes (100KB+ per font)
* Base64 encoding adds ~33% overhead
* May include glyphs not used in the document

Automatic Font Fallback Chains
-------------------------------

When psd2svg embeds fonts, it automatically generates CSS font fallback chains to handle font substitutions gracefully.

How It Works
~~~~~~~~~~~~

When a requested font is not available on the system, font rendering engines substitute it with another font. psd2svg detects these substitutions and generates proper CSS fallback chains:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")  # Uses "Arial"
   document = SVGDocument.from_psd(psdimage)
   document.save("output.svg", embed_fonts=True)

If Arial is not installed and the system substitutes DejaVu Sans, the generated SVG will contain:

.. code-block:: css

   /* CSS fallback chain in SVG */
   font-family: 'Arial', 'DejaVu Sans';

   /* @font-face embeds DejaVu Sans (the actual font) */
   @font-face {
     font-family: 'DejaVu Sans';
     src: url(data:font/ttf;base64,...);
   }

**Benefits:**

* **Correct rendering**: Browser uses the embedded fallback font when primary font unavailable
* **Transparent**: Automatic detection and handling of font substitutions
* **No configuration**: Works out-of-the-box with fontconfig (Linux/macOS)

**Logging:**

Font substitutions are logged at INFO level:

.. code-block:: text

   INFO Font fallback: 'Arial' → 'DejaVu Sans'

Platform Behavior
~~~~~~~~~~~~~~~~~

**Linux/macOS** (with fontconfig):

* Automatically detects font substitutions
* Generates fallback chains for all substituted fonts
* Embeds actual system fonts in SVG
* Uses fontconfig for font file discovery

**Windows** (with Windows registry):

* Automatically detects font substitutions
* Generates fallback chains for all substituted fonts
* Embeds actual system fonts in SVG
* Uses Windows registry + fontTools parsing for font file discovery
* Supports both TrueType and OpenType fonts

Note About Generic Families
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

psd2svg does not automatically add generic font families (``sans-serif``, ``serif``, ``monospace``) to fallback chains. Determining the appropriate generic family automatically is non-trivial and would require font classification heuristics or external databases.

You can manually add generic families in post-processing if needed.

Custom Font Mapping
-------------------

For fonts not in the default mapping (572 common fonts), you can provide custom font mappings to enable text conversion.

Understanding Font Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~

psd2svg uses PostScript font names (e.g., "ArialMT", "TimesNewRomanPSMT") to resolve fonts. The mapping provides:

* **Font family** name (e.g., "Arial")
* **Font style** (e.g., "Regular", "Bold")
* **Font weight** (numeric value, 0-250, where 80 = Regular, 200 = Bold)

This information is used to generate SVG ``<text>`` elements with correct font properties.

**Font Resolution Priority:**

1. Custom mapping (if provided via ``font_mapping`` parameter)
2. Default static mapping (572 common fonts)
3. Platform-specific font resolution for file path discovery:

   * **Linux/macOS**: fontconfig query
   * **Windows**: Windows registry + fontTools parsing

Custom mappings take priority, allowing you to override built-in font resolution.

Generating Custom Mappings
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the CLI tool to extract fonts from your PSD files:

.. code-block:: bash

   # Extract all fonts from a PSD file
   python -m psd2svg.tools.generate_font_mapping input.psd -o fonts.json

   # Show only fonts NOT in default mapping
   python -m psd2svg.tools.generate_font_mapping input.psd --only-missing

   # Query fontconfig to auto-fill font details (Linux/macOS)
   python -m psd2svg.tools.generate_font_mapping input.psd --query-fontconfig -o fonts.json

   # Multiple PSD files
   python -m psd2svg.tools.generate_font_mapping *.psd -o fonts.json

   # Python format output (for embedding in code)
   python -m psd2svg.tools.generate_font_mapping input.psd -o fonts.py --format python

   # Verbose mode shows progress and font details
   python -m psd2svg.tools.generate_font_mapping input.psd -v

**Output Formats:**

* ``json`` (default): JSON file for use with Python API
* ``python``: Python dict literal for embedding in source code

**What the tool does:**

1. Opens PSD file(s) and scans all visible text layers
2. Extracts PostScript font names actually used
3. Checks against default mapping
4. Optionally queries fontconfig for font details
5. Generates mapping file in requested format

Using Custom Mappings
~~~~~~~~~~~~~~~~~~~~~~

Load and use custom font mappings in your conversion:

.. code-block:: python

   import json
   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   # Load custom font mapping from JSON
   with open("fonts.json") as f:
       custom_fonts = json.load(f)

   # Use custom mapping in conversion
   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, font_mapping=custom_fonts)
   document.save("output.svg")

**Font Mapping Structure:**

.. code-block:: json

   {
       "MyCustomFont-Regular": {
           "family": "My Custom Font",
           "style": "Regular",
           "weight": 80.0,
           "_comment": "Optional comment for documentation"
       },
       "MyCustomFont-Bold": {
           "family": "My Custom Font",
           "style": "Bold",
           "weight": 200.0
       },
       "AnotherFont-Italic": {
           "family": "Another Font",
           "style": "Italic",
           "weight": 80.0
       }
   }

**Required fields:**

* ``family`` (string): Font family name
* ``style`` (string): Font style (e.g., "Regular", "Bold", "Italic")
* ``weight`` (float): Font weight (0-250, typical: 80 = Regular, 200 = Bold)

**Optional fields:**

* ``_comment`` (string): Human-readable comment (ignored during processing)

When to Use Custom Mappings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom font mappings are useful when:

* **Using custom or proprietary fonts** not in the default mapping
* **Working with uncommon fonts** in PSD files
* **Overriding default font resolution** for specific fonts
* **Working on Windows** to enable text conversion for specific fonts
* **Ensuring consistent font naming** across different systems

**Example Use Cases:**

1. **Corporate branding fonts**: Map proprietary brand fonts used in PSD files
2. **Web font services**: Map PostScript names to web font equivalents
3. **Font substitution**: Override mappings to use different fonts in output
4. **Multi-language projects**: Add fonts for specific writing systems

Font Embedding with Custom Mappings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom mappings enable text conversion but don't provide font file paths. For font embedding, the ``FontInfo.resolve()`` method automatically queries platform-specific font resolution:

**On Linux/macOS:**

Automatically queries fontconfig during conversion:

* Resolves fonts to actual system fonts
* Detects substitutions and generates fallback chains
* Enables font embedding with ``embed_fonts=True``

**On Windows:**

Automatically queries Windows registry + fontTools parsing during conversion:

* Resolves fonts to actual system fonts
* Detects substitutions and generates fallback chains
* Enables font embedding with ``embed_fonts=True``

.. code-block:: python

   # Font embedding works automatically on all platforms
   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(
       psdimage,
       font_mapping=custom_fonts,  # Provides font metadata
       embed_fonts=True             # Fonts resolved and embedded automatically
   )

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
   document = SVGDocument.from_psd(psdimage)

   # Save with WOFF2 subsetting and font embedding
   document.save("output.svg", embed_fonts=True, font_format="woff2")

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
   document = SVGDocument.from_psd(psdimage)

   # Get SVG string with WOFF2 subsetting and font embedding
   svg_string = document.tostring(embed_fonts=True, font_format="woff2")

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

1. **Verify fontTools is installed:**

   .. code-block:: python

      import fontTools
      print(fontTools.__version__)

   If not installed, reinstall psd2svg:

   .. code-block:: bash

      pip install --force-reinstall psd2svg

2. **Check for errors** in the console output

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

Rasterization Performance
~~~~~~~~~~~~~~~~~~~~~~~~~

When using ``rasterize()`` with PlaywrightRasterizer, psd2svg automatically optimizes font handling for 60-80% faster performance:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd2svg.rasterizer import PlaywrightRasterizer
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)

   # Automatic optimization: uses file:// URLs instead of data URIs
   rasterizer = PlaywrightRasterizer(dpi=144)
   image = document.rasterize(rasterizer)
   image.save("output.png")

**How it works:**

* For saved SVG files (``save()``/``tostring()``), fonts are embedded as base64 data URIs (portable but slower to generate)
* For transient rasterization (``rasterize()`` with PlaywrightRasterizer), fonts use local ``file://`` URLs (no encoding overhead)
* Optimization is automatic, transparent, and requires no configuration
* Font resolution and fallback chains work identically in both modes

**Performance impact:**

* **60-80% faster rasterization** - Skips font encoding/subsetting overhead
* **99% smaller SVG strings** - No base64 encoding (transient SVG only, not saved files)
* **Lower memory usage** - No font data caching needed for rasterization
* **More robust** - Avoids potential font subsetting errors during rasterization

**When optimization applies:**

* ✅ Using ``rasterize()`` method with ``PlaywrightRasterizer``
* ✅ Document has text elements with font-family attributes
* ✅ Fonts successfully resolved to system font files
* ❌ Does NOT apply to ``save()`` or ``tostring()`` (those still use data URIs for portability)

**Note:** This optimization only affects the internal SVG representation used for rasterization. Saved SVG files (``save()``/``tostring()``) continue to use data URIs for maximum portability and self-containment.

Best Practices
~~~~~~~~~~~~~~

1. **Use WOFF2 for web** - Best compression and broad browser support
2. **Subset by default** - No reason not to with WOFF2
3. **Cache font files** - If using external fonts, leverage HTTP caching
4. **Limit font families** - Each font adds to file size
5. **Consider system fonts** - For non-critical text, use web-safe fonts
6. **Use PlaywrightRasterizer for faster rasterization** - Automatic 60-80% speedup for font-heavy documents

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
   document = SVGDocument.from_psd(psdimage)

   # Optimize for web: WOFF2 subsetting, external images, font embedding
   document.save(
       "output.svg",
       embed_fonts=True,
       font_format="woff2",
       image_prefix="images/img",
       image_format="webp",
       enable_title=False  # Remove layer names
   )

This produces the smallest possible file while maintaining visual fidelity.
