Rasterizers
===========

The psd2svg package uses resvg for converting SVG documents to raster images (PNG, JPEG, etc.).

Overview
--------

The rasterizer system provides a high-performance interface for converting SVG to PIL Image objects using the resvg rendering engine.

Platform Support
~~~~~~~~~~~~~~~~

**psd2svg Core Platform Support:**

* **Linux**: Full support for all features including text layer conversion
* **macOS**: Full support for all features including text layer conversion
* **Windows**: Supported - text layers are rasterized as images (fontconfig not available)

**Text Layer Conversion:**

Text layer conversion requires fontconfig for font resolution:

* **Linux/macOS**: Text layers are converted to native SVG ``<text>`` elements (fontconfig installed automatically)
* **Windows**: Text layers are automatically rasterized as images (fontconfig not available on Windows)
* **All platforms**: Can explicitly disable text conversion with ``enable_text=False``

**Rasterizer Platform Support:**

* **ResvgRasterizer**: Supports Linux, macOS, and Windows
* **PlaywrightRasterizer**: Supports Linux, macOS, and Windows (browsers automatically downloaded)

Resvg Rasterizer
----------------

Fast, accurate, and pure Rust implementation via resvg-py.

**Pros:**

* Fastest performance
* High accuracy
* No browser dependencies
* Simple installation
* Production-ready

**Limitations:**

* Does not support SVG ``<foreignObject>`` elements (they are ignored during rendering)
* Does not support some SVG 2.0 features (e.g., ``text-orientation: upright``, ``dominant-baseline`` for vertical text)

**Note:** If you need ``<foreignObject>`` support for text wrapping, use PlaywrightRasterizer instead (see below).

**Installation:**

The ``resvg-py`` package is included as a dependency when you install psd2svg:

.. code-block:: bash

   pip install psd2svg

**Usage:**

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer

   # Create rasterizer instance
   rasterizer = ResvgRasterizer(dpi=96)

   # Rasterize from file
   image = rasterizer.from_file('input.svg')
   image.save('output.png')

   # Rasterize from string
   svg_string = '<svg>...</svg>'
   image = rasterizer.from_string(svg_string)
   image.save('output.png')

Using with SVGDocument
----------------------

The ``SVGDocument`` class has a built-in ``rasterize()`` method that uses resvg:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   # Load PSD and convert to SVG
   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)

   # Rasterize using default settings
   image = document.rasterize()
   image.save('output.png')

   # Rasterize with custom DPI
   image = document.rasterize(dpi=300)
   image.save('output_high_res.png')

API Reference
-------------

ResvgRasterizer
~~~~~~~~~~~~~~~

.. code-block:: python

   class ResvgRasterizer(BaseRasterizer):
       def __init__(self, dpi: int = 0) -> None:
           """Initialize the resvg rasterizer.

           Args:
               dpi: Dots per inch for rendering. If 0 (default), uses resvg's
                   default of 96 DPI. Higher values produce larger, higher
                   resolution images (e.g., 300 DPI for print quality).
           """

       def from_file(self, filepath: str) -> Image.Image:
           """Rasterize an SVG file to a PIL Image.

           Args:
               filepath: Path to the SVG file to rasterize.

           Returns:
               PIL Image object in RGBA mode containing the rasterized SVG.

           Raises:
               FileNotFoundError: If the SVG file does not exist.
               ValueError: If the SVG content is invalid.
           """

       def from_string(self, svg_content: Union[str, bytes]) -> Image.Image:
           """Rasterize SVG content from a string to a PIL Image.

           Args:
               svg_content: SVG content as string or bytes.

           Returns:
               PIL Image object in RGBA mode containing the rasterized SVG.

           Raises:
               ValueError: If the SVG content is invalid.
           """

Examples
--------

Basic Rasterization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer

   rasterizer = ResvgRasterizer()
   image = rasterizer.from_file('input.svg')
   image.save('output.png')

High DPI Rendering
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer

   # Render at 300 DPI for print quality
   rasterizer = ResvgRasterizer(dpi=300)
   image = rasterizer.from_file('input.svg')
   image.save('output_print.png')

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from psd2svg.rasterizer import ResvgRasterizer

   rasterizer = ResvgRasterizer()
   svg_dir = Path("svg_files")
   png_dir = Path("png_output")
   png_dir.mkdir(exist_ok=True)

   for svg_file in svg_dir.glob("*.svg"):
       output_path = png_dir / f"{svg_file.stem}.png"
       image = rasterizer.from_file(str(svg_file))
       image.save(output_path)

Different Output Formats
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer

   rasterizer = ResvgRasterizer()
   image = rasterizer.from_file('input.svg')

   # PNG - lossless
   image.save('output.png', format='PNG', optimize=True)

   # JPEG - lossy
   image.convert('RGB').save('output.jpg', format='JPEG', quality=95)

   # WebP - modern format
   image.save('output.webp', format='WEBP', quality=90)

Troubleshooting
---------------

Installation Issues
~~~~~~~~~~~~~~~~~~~

If resvg-py fails to install:

.. code-block:: bash

   # Ensure you have a compatible Python version
   python --version  # Should be 3.10+

   # Upgrade pip
   pip install --upgrade pip

   # Install resvg-py
   pip install resvg-py

Known Issues with resvg-py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The underlying resvg-py library has some stability issues with edge cases:

**Crashes (SIGABRT):**

The resvg-py library may crash with SIGABRT instead of raising proper Python exceptions when encountering:

* **Severely malformed SVG content** - Invalid or corrupted SVG markup
* **Missing files** - Attempting to load non-existent SVG files
* **Empty SVG documents** - SVG files with 0x0 dimensions

**Impact:**

These crashes cannot be caught with Python's exception handling (``try/except``), which means:

* Your application may terminate unexpectedly
* Error recovery is not possible for these cases
* Proper error messages are not available

**Workarounds:**

1. **Validate SVG before rasterizing** - Use a separate XML parser to validate SVG content:

   .. code-block:: python

      import xml.etree.ElementTree as ET
      from psd2svg.rasterizer import ResvgRasterizer

      def safe_rasterize(svg_path):
          # Validate SVG first
          try:
              tree = ET.parse(svg_path)
              root = tree.getroot()
              if root.tag != '{http://www.w3.org/2000/svg}svg':
                  return None
          except ET.ParseError:
              return None

          # Now safe to rasterize
          rasterizer = ResvgRasterizer()
          return rasterizer.from_file(svg_path)

2. **Check file existence** - Verify files exist before attempting to load:

   .. code-block:: python

      import os
      from psd2svg.rasterizer import ResvgRasterizer

      def safe_rasterize_file(svg_path):
          if not os.path.exists(svg_path):
              raise FileNotFoundError(f"SVG file not found: {svg_path}")

          rasterizer = ResvgRasterizer()
          return rasterizer.from_file(svg_path)

3. **Use PlaywrightRasterizer for edge cases** - The browser-based rasterizer handles errors more gracefully (see Playwright Rasterizer section below)

**Status:**

These are limitations of the underlying resvg-py wrapper library, not psd2svg. For production use, implement proper validation and error handling as shown above.

Resizing Output Images
~~~~~~~~~~~~~~~~~~~~~~

Resvg rasterizes SVG at the intrinsic size defined in the SVG document.
If you need specific dimensions, consider resizing the output image using PIL:

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer
   from PIL import Image

   rasterizer = ResvgRasterizer()
   image = rasterizer.from_file('input.svg')

   # Resize to specific dimensions
   resized = image.resize((800, 600), Image.Resampling.LANCZOS)
   resized.save('output_800x600.png')

Custom Background
~~~~~~~~~~~~~~~~~

By default, rasterized images have a transparent background. To add a custom background:

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer
   from PIL import Image

   rasterizer = ResvgRasterizer()
   image = rasterizer.from_file('input.svg')

   # Create white background
   background = Image.new('RGB', image.size, (255, 255, 255))
   background.paste(image, (0, 0), image)
   background.save('output_white_bg.png')

Playwright Rasterizer
----------------------

Browser-based SVG rasterizer with full SVG 2.0 support using Playwright/Chromium.

**Installation:**

The Playwright rasterizer requires the ``browser`` optional dependency group:

.. code-block:: bash

   pip install psd2svg[browser]
   playwright install chromium

**Pros:**

* Full SVG 2.0 support
* Supports ``<foreignObject>`` elements (text wrapping)
* Excellent support for advanced SVG features
* Browser-accurate rendering
* Better support for variable fonts

**Cons:**

* Slower than ResvgRasterizer
* Requires Chromium installation (~200MB)
* Higher memory usage
* Not suitable for serverless environments

**When to use:**

* Testing SVG 2.0 features (vertical text, text-orientation, dominant-baseline)
* Quality assurance against browser rendering
* Text wrapping with ``<foreignObject>``
* Variable font rendering (resvg-py has known issues)
* Advanced SVG features not supported by resvg

Usage
~~~~~

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from psd2svg.rasterizer import PlaywrightRasterizer

   # Use as context manager (automatically cleans up browser)
   with PlaywrightRasterizer(dpi=96) as rasterizer:
       image = rasterizer.from_file('input.svg')
       image.save('output.png')

**Important:** Always use PlaywrightRasterizer as a context manager to ensure proper browser cleanup.

With SVGDocument
^^^^^^^^^^^^^^^^

.. code-block:: python

   from psd2svg import SVGDocument
   from psd2svg.rasterizer import PlaywrightRasterizer
   from psd_tools import PSDImage

   psdimage = PSDImage.open('input.psd')
   document = SVGDocument.from_psd(psdimage)

   # Rasterize using Playwright
   with PlaywrightRasterizer(dpi=96) as rasterizer:
       image = document.rasterize(rasterizer=rasterizer)
       image.save('output.png')

Rasterizing from String
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from psd2svg.rasterizer import PlaywrightRasterizer

   svg_string = '<svg>...</svg>'

   with PlaywrightRasterizer(dpi=96) as rasterizer:
       image = rasterizer.from_string(svg_string)
       image.save('output.png')

API Reference
^^^^^^^^^^^^^

.. code-block:: python

   class PlaywrightRasterizer(BaseRasterizer):
       def __init__(self, dpi: int = 0) -> None:
           """Initialize the Playwright rasterizer.

           Args:
               dpi: Dots per inch for rendering. If 0 (default), uses 96 DPI.
                   Higher values produce larger, higher resolution images.
           """

       def __enter__(self) -> PlaywrightRasterizer:
           """Enter context manager - starts browser."""

       def __exit__(self, *args) -> None:
           """Exit context manager - closes browser and cleans up resources."""

       def from_file(self, filepath: str) -> Image.Image:
           """Rasterize an SVG file to a PIL Image.

           Args:
               filepath: Path to the SVG file to rasterize.

           Returns:
               PIL Image object in RGBA mode containing the rasterized SVG.
           """

       def from_string(self, svg_content: Union[str, bytes]) -> Image.Image:
           """Rasterize SVG content from a string to a PIL Image.

           Args:
               svg_content: SVG content as string or bytes.

           Returns:
               PIL Image object in RGBA mode containing the rasterized SVG.
           """

Examples
~~~~~~~~

High DPI Rendering
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from psd2svg.rasterizer import PlaywrightRasterizer

   # Render at 300 DPI for print quality
   with PlaywrightRasterizer(dpi=300) as rasterizer:
       image = rasterizer.from_file('input.svg')
       image.save('output_print.png')

Batch Processing
^^^^^^^^^^^^^^^^

.. code-block:: python

   from pathlib import Path
   from psd2svg.rasterizer import PlaywrightRasterizer

   svg_dir = Path("svg_files")
   png_dir = Path("png_output")
   png_dir.mkdir(exist_ok=True)

   # Reuse browser instance for better performance
   with PlaywrightRasterizer() as rasterizer:
       for svg_file in svg_dir.glob("*.svg"):
           output_path = png_dir / f"{svg_file.stem}.png"
           image = rasterizer.from_file(str(svg_file))
           image.save(output_path)

Testing SVG 2.0 Features
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from psd2svg import SVGDocument
   from psd2svg.rasterizer import PlaywrightRasterizer
   from psd_tools import PSDImage

   # Convert PSD with vertical text (SVG 2.0 feature)
   psdimage = PSDImage.open('vertical_text.psd')
   document = SVGDocument.from_psd(psdimage)

   # Render with Playwright (supports SVG 2.0)
   with PlaywrightRasterizer() as rasterizer:
       image = document.rasterize(rasterizer=rasterizer)
       image.save('output_vertical_text.png')

Comparing Rasterizers
---------------------

Feature Comparison
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Feature
     - ResvgRasterizer
     - PlaywrightRasterizer
   * - Performance
     - Fast (Rust-based)
     - Slower (browser-based)
   * - Installation Size
     - Small (~5MB)
     - Large (~200MB)
   * - SVG 1.1 Support
     - Excellent
     - Excellent
   * - SVG 2.0 Support
     - Partial
     - Full
   * - ``<foreignObject>``
     - Not supported
     - Supported
   * - Variable Fonts
     - Known issues
     - Works correctly
   * - Memory Usage
     - Low
     - Higher
   * - Serverless Friendly
     - Yes
     - No
   * - Production Ready
     - Yes
     - Yes

When to Use Which
~~~~~~~~~~~~~~~~~

**Use ResvgRasterizer when:**

* Performance is critical
* Deploying to serverless environments
* Memory constraints exist
* Standard SVG features are sufficient
* Installation size matters

**Use PlaywrightRasterizer when:**

* SVG 2.0 features are required
* Text wrapping with ``<foreignObject>`` is needed
* Variable font rendering is important
* Browser-accurate rendering is required
* Testing/QA against browser rendering

**Example: Fallback Strategy:**

.. code-block:: python

   from psd2svg import SVGDocument
   from psd2svg.rasterizer import ResvgRasterizer
   from psd_tools import PSDImage

   psdimage = PSDImage.open('input.psd')
   document = SVGDocument.from_psd(psdimage)

   # Try ResvgRasterizer first (faster)
   try:
       image = document.rasterize()
       image.save('output.png')
   except Exception:
       # Fall back to Playwright if needed
       from psd2svg.rasterizer import PlaywrightRasterizer
       with PlaywrightRasterizer() as rasterizer:
           image = document.rasterize(rasterizer=rasterizer)
           image.save('output.png')

Performance Tips
~~~~~~~~~~~~~~~~

**For ResvgRasterizer:**

* Reuse rasterizer instances when possible
* Use appropriate DPI (higher DPI = larger output)
* Validate SVG before rasterizing (see Known Issues section)

**For PlaywrightRasterizer:**

* Reuse browser instance for batch operations (use context manager once)
* Close browser when done (use context manager)
* Minimize page loads (process multiple SVGs in one session)
* Consider headless mode overhead

Troubleshooting
---------------

PlaywrightRasterizer Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Browser not installed:**

.. code-block:: bash

   playwright install chromium

**Import error:**

Ensure the ``browser`` group is installed:

.. code-block:: bash

   pip install psd2svg[browser]

**Timeout errors:**

For large or complex SVGs, increase timeout:

.. code-block:: python

   with PlaywrightRasterizer(dpi=96) as rasterizer:
       # Timeout is handled internally
       image = rasterizer.from_file('large.svg')

**Memory issues:**

Close and reopen browser periodically for long-running processes:

.. code-block:: python

   from psd2svg.rasterizer import PlaywrightRasterizer

   svg_files = list(Path("svg_files").glob("*.svg"))

   # Process in batches to manage memory
   batch_size = 50
   for i in range(0, len(svg_files), batch_size):
       batch = svg_files[i:i+batch_size]
       with PlaywrightRasterizer() as rasterizer:
           for svg_file in batch:
               image = rasterizer.from_file(str(svg_file))
               image.save(f"{svg_file.stem}.png")
