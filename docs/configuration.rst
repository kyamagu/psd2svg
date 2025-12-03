Configuration Options
=====================

This guide covers advanced configuration options for customizing SVG output.

Title Elements
--------------

Overview
~~~~~~~~

By default, each layer in the SVG includes a ``<title>`` element containing the Photoshop layer name. This provides:

* Layer identification in SVG editors
* Tooltips when hovering in browsers
* Accessibility improvements
* Better debugging experience

Example output:

.. code-block:: xml

   <g id="layer-1">
     <title>Background Layer</title>
     <!-- layer content -->
   </g>

Disabling Titles
~~~~~~~~~~~~~~~~

Title elements increase file size. You can disable them for production:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, enable_title=False)
   document.save("output.svg")

**Command Line:**

.. code-block:: bash

   psd2svg input.psd output.svg --no-title

**When to disable:**

* Production builds (file size matters)
* Minified output
* Layer names contain sensitive information
* SVG will not be edited further

**When to keep enabled:**

* Development/debugging
* SVG will be opened in editors
* Accessibility is important
* File size is not critical

Text Letter Spacing
-------------------

Overview
~~~~~~~~

Photoshop and SVG renderers may have slightly different default letter spacing due to differences in kerning algorithms and text layout engines.

The ``text_letter_spacing_offset`` parameter compensates for these differences by adding a global offset to all letter-spacing values:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")

   # Increase letter spacing by 0.5 pixels
   document = SVGDocument.from_psd(
       psdimage,
       text_letter_spacing_offset=0.5
   )
   document.save("output.svg")

   # Decrease letter spacing by 0.015 pixels
   document = SVGDocument.from_psd(
       psdimage,
       text_letter_spacing_offset=-0.015
   )
   document.save("output.svg")

**Command Line:**

.. code-block:: bash

   # Increase letter spacing
   psd2svg input.psd output.svg --text-letter-spacing-offset 0.5

   # Decrease letter spacing
   psd2svg input.psd output.svg --text-letter-spacing-offset -0.015

How It Works
~~~~~~~~~~~~

The offset (in pixels) is added to all letter-spacing values:

* **Positive values** increase spacing between letters
* **Negative values** decrease spacing between letters
* **Zero** (default) applies no adjustment

**Example:**

If Photoshop specifies ``letter-spacing: 2px`` and you set ``text_letter_spacing_offset=-0.5``, the SVG will have ``letter-spacing: 1.5px``.

Finding the Right Value
~~~~~~~~~~~~~~~~~~~~~~~

Experiment with different values to find the best match for your specific fonts and target renderers:

1. **Start with 0** (no adjustment)
2. **Compare visually** - Render SVG vs Photoshop side-by-side
3. **Adjust incrementally** - Try values like ±0.01, ±0.05, ±0.1
4. **Test in target environment** - Check rendering in your target browser/viewer

**Typical values:**

* **-0.015 to -0.05** - Tighten spacing (common for web fonts)
* **0** - No adjustment (default)
* **0.01 to 0.1** - Loosen spacing

Class Attributes
----------------

Overview
~~~~~~~~

For debugging purposes, you can enable CSS class attributes on SVG elements:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, enable_class=True)
   document.save("output.svg")

**Result:** SVG elements include class attributes for debugging:

.. code-block:: xml

   <g class="layer" id="layer-1">
     <title>Background</title>
     <rect class="shape" ... />
   </g>

**Purpose:**

* Easier CSS targeting in browsers
* Better debugging in browser dev tools
* Identifying element types in SVG editors

**Warning:** Class attributes are **disabled by default** because they:

* Increase file size
* Are not useful in production
* May conflict with existing CSS

Only enable for debugging purposes.

Text Wrapping Mode
------------------

Overview
~~~~~~~~

psd2svg provides different strategies for handling text that wraps within bounding boxes:

.. code-block:: python

   from psd2svg import SVGDocument, TextWrappingMode
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")

   # Use foreignObject for text wrapping (experimental)
   document = SVGDocument.from_psd(
       psdimage,
       text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
   )
   document.save("output.svg")

Text Wrapping Modes
~~~~~~~~~~~~~~~~~~~

**TextWrappingMode.NONE** (default):

* Converts text to ``<text>`` elements without wrapping
* Text may overflow bounding box
* Best compatibility
* Recommended for most use cases

**TextWrappingMode.FOREIGN_OBJECT**:

* Uses ``<foreignObject>`` with HTML for text wrapping
* Preserves text wrapping from Photoshop
* Requires SVG 1.1+ support
* May not render in some viewers (e.g., resvg)

**Example:**

.. code-block:: python

   from psd2svg import SVGDocument, TextWrappingMode
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")

   # Default: no wrapping
   document = SVGDocument.from_psd(psdimage)

   # Experimental: use foreignObject for wrapping
   document = SVGDocument.from_psd(
       psdimage,
       text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
   )

**Limitations:**

* ``<foreignObject>`` is not supported by ResvgRasterizer (ignored during rendering)
* Text layout may differ slightly from Photoshop
* Font metrics affect wrapping behavior

**Recommendation:** Use default mode (NONE) unless you specifically need text wrapping and target browsers/viewers that support ``<foreignObject>``.

Optimization
------------

SVG Optimization
~~~~~~~~~~~~~~~~

By default, psd2svg optimizes SVG output by consolidating all ``<defs>`` elements into a single global ``<defs>`` section:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)

   # Optimized (default)
   document.save("output.svg", optimize=True)

   # Unoptimized (preserves original structure)
   document.save("output.svg", optimize=False)

**Optimization benefits:**

* Consolidates duplicate definitions
* Reduces file size
* Cleaner SVG structure
* Better compression

**Disable optimization when:**

* Debugging SVG structure
* Need to preserve exact element hierarchy
* Working with SVG editors that expect specific structure

Live Shapes
-----------

Overview
~~~~~~~~

psd2svg can convert Photoshop live shapes (rectangles, ellipses) to native SVG shape primitives (``<rect>``, ``<circle>``, ``<ellipse>``):

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")

   # Convert live shapes to primitives (default)
   document = SVGDocument.from_psd(psdimage, enable_live_shapes=True)

   # Convert all shapes to paths
   document = SVGDocument.from_psd(psdimage, enable_live_shapes=False)

**Command Line:**

.. code-block:: bash

   # Disable live shapes (use paths instead)
   psd2svg input.psd output.svg --no-live-shapes

Benefits of Live Shapes
~~~~~~~~~~~~~~~~~~~~~~~~

**Enabled (default):**

* Semantic SVG elements (``<rect>``, ``<circle>``)
* Easier to edit in SVG editors
* Better for animation
* Clearer intent

**Disabled:**

* All shapes become ``<path>`` elements
* More compact in some cases
* Uniform structure
* Better for complex transformations

**Recommendation:** Keep enabled (default) unless you need all shapes as paths.

Performance Tips
----------------

Reduce Conversion Time
~~~~~~~~~~~~~~~~~~~~~~

1. **Disable features you don't need:**

   .. code-block:: python

      document = SVGDocument.from_psd(
          psdimage,
          enable_text=False,      # Rasterize text
          enable_title=False,     # No titles
          enable_live_shapes=False  # Use paths
      )

2. **Use external images:**

   .. code-block:: python

      document.save(
          "output.svg",
          image_prefix="images/img"  # Faster than base64 encoding
      )

3. **Simplify PSD:**

   * Merge unnecessary layers
   * Flatten complex effects
   * Reduce layer count

Reduce File Size
~~~~~~~~~~~~~~~~

1. **Disable titles:**

   .. code-block:: python

      document = SVGDocument.from_psd(psdimage, enable_title=False)

2. **Use external images:**

   .. code-block:: python

      document.save("output.svg", image_prefix="images/img")

3. **Use WebP format:**

   .. code-block:: python

      document.save("output.svg", image_format="webp")

4. **Enable optimization:**

   .. code-block:: python

      document.save("output.svg", optimize=True)

5. **Font subsetting:**

   .. code-block:: python

      document.save("output.svg", font_format="woff2")

**Combined example:**

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, enable_title=False)

   document.save(
       "output.svg",
       image_prefix="images/img",
       image_format="webp",
       font_format="woff2",
       optimize=True
   )

Thread Safety
-------------

Important Warning
~~~~~~~~~~~~~~~~~

**psd2svg APIs are NOT thread-safe.**

Do not share ``SVGDocument`` instances across threads or call conversion methods concurrently from multiple threads.

**Unsafe:**

.. code-block:: python

   from concurrent.futures import ThreadPoolExecutor
   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)  # Shared instance

   # DON'T DO THIS - Not thread-safe!
   with ThreadPoolExecutor() as executor:
       executor.submit(document.save, "output1.svg")
       executor.submit(document.save, "output2.svg")

**Safe approach:**

.. code-block:: python

   from concurrent.futures import ThreadPoolExecutor
   from psd2svg import convert

   def convert_file(input_path, output_path):
       """Each thread gets its own conversion instance."""
       convert(input_path, output_path)

   # Safe - Each conversion is independent
   with ThreadPoolExecutor() as executor:
       executor.submit(convert_file, "input1.psd", "output1.svg")
       executor.submit(convert_file, "input2.psd", "output2.svg")

**Recommendation:** Use multiprocessing instead of threading for parallel conversions.

Error Handling
--------------

Best Practices
~~~~~~~~~~~~~~

Always wrap conversion operations in try-except blocks:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   try:
       psdimage = PSDImage.open("input.psd")
       document = SVGDocument.from_psd(psdimage)
       document.save("output.svg")
   except FileNotFoundError:
       print("PSD file not found")
   except ValueError as e:
       print(f"Invalid PSD format: {e}")
   except Exception as e:
       print(f"Conversion failed: {e}")

**Common exceptions:**

* ``FileNotFoundError`` - Input file doesn't exist
* ``ValueError`` - Invalid PSD format or corrupted file
* ``PermissionError`` - Cannot write output file
* ``OSError`` - Disk full or I/O error

Logging
~~~~~~~

Enable logging to debug conversion issues:

.. code-block:: python

   import logging
   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)
   document.save("output.svg")

This will print detailed information about the conversion process, including:

* Layer processing
* Font resolution
* Rasterization decisions
* Resource generation
