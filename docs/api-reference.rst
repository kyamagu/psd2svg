API Reference
=============

This section documents the public API of psd2svg.

Main API
--------

convert()
~~~~~~~~~

.. autofunction:: psd2svg.convert

SVGDocument
~~~~~~~~~~~

.. autoclass:: psd2svg.SVGDocument
   :members:
   :special-members: __init__
   :undoc-members:
   :show-inheritance:

Rasterizers
-----------

Base Rasterizer
~~~~~~~~~~~~~~~

.. autoclass:: psd2svg.rasterizer.BaseRasterizer
   :members:
   :undoc-members:
   :show-inheritance:

Resvg Rasterizer
~~~~~~~~~~~~~~~~

.. autoclass:: psd2svg.rasterizer.ResvgRasterizer
   :members:
   :undoc-members:
   :show-inheritance:

Fast, production-ready SVG rasterizer using the resvg rendering engine.

Example:

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer

   # Create rasterizer instance
   rasterizer = ResvgRasterizer(dpi=96)

   # Rasterize from string
   image = rasterizer.from_string(svg_string)

   # Rasterize from file
   image = rasterizer.from_file('input.svg')

Playwright Rasterizer
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: psd2svg.rasterizer.PlaywrightRasterizer
   :members:
   :undoc-members:
   :show-inheritance:

Browser-based SVG rasterizer with full SVG 2.0 support using Playwright/Chromium.

**Installation:**

.. code-block:: bash

   pip install psd2svg[browser]
   playwright install chromium

**Example:**

.. code-block:: python

   from psd2svg.rasterizer import PlaywrightRasterizer

   # Use as context manager (automatically cleans up browser)
   with PlaywrightRasterizer(dpi=96) as rasterizer:
       image = rasterizer.from_file('input.svg')
       image.save('output.png')

   # Or with SVGDocument
   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open('input.psd')
   document = SVGDocument.from_psd(psdimage)

   with PlaywrightRasterizer(dpi=96) as rasterizer:
       image = document.rasterize(rasterizer=rasterizer)
       image.save('output.png')

**When to use:**

* Testing SVG 2.0 features (vertical text, text-orientation, dominant-baseline)
* Quality assurance against browser rendering
* Better support for advanced SVG features not supported by resvg

Utility Modules
---------------

SVG Utilities
~~~~~~~~~~~~~

.. automodule:: psd2svg.svg_utils
   :members:
   :undoc-members:
   :show-inheritance:

Image Utilities
~~~~~~~~~~~~~~~

.. automodule:: psd2svg.image_utils
   :members:
   :undoc-members:
   :show-inheritance:

Font Subsetting
~~~~~~~~~~~~~~~~

.. automodule:: psd2svg.font_subsetting
   :members:
   :undoc-members:
   :show-inheritance:

Font subsetting reduces embedded font file sizes by 90%+ by including only the glyphs actually used in the SVG.

**Note:** Font subsetting is enabled by default when embedding fonts. The required ``fonttools`` package is automatically installed with psd2svg.

**Usage Example:**

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

**Note:** This module is typically used internally by ``SVGDocument.save()`` and ``tostring()`` methods. Direct usage is only needed for advanced use cases.

Quality Evaluation
~~~~~~~~~~~~~~~~~~

.. automodule:: psd2svg.eval
   :members:
   :undoc-members:
   :show-inheritance:

Utilities for evaluating the quality of PSD to SVG conversion by comparing rasterized outputs.

**Usage Example:**

.. code-block:: python

   from psd2svg.eval import compute_conversion_quality, create_diff_image
   from psd_tools import PSDImage

   # Load PSD
   psdimage = PSDImage.open("input.psd")

   # Compute quality score (0.0 to 1.0, higher is better)
   score = compute_conversion_quality(psdimage, metric="mse")
   print(f"Quality score: {score:.4f}")

   # Create visual diff image for debugging
   diff_image = create_diff_image(psdimage, amplify=5.0)
   diff_image.save("diff.png")

**Supported metrics:**

* ``mse`` - Mean Squared Error (default)
* ``rmse`` - Root Mean Squared Error
* ``psnr`` - Peak Signal-to-Noise Ratio
* ``ssim`` - Structural Similarity Index

**Note:** This module is primarily intended for testing and quality assurance purposes.

Internal Modules
----------------

The following modules are internal implementation details and may change without notice.
They are documented here for reference but should not be used directly.

Core Converter
~~~~~~~~~~~~~~

.. automodule:: psd2svg.core.converter
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:

Layer Converter
~~~~~~~~~~~~~~~

.. automodule:: psd2svg.core.layer
   :members:
   :undoc-members:
   :show-inheritance:

Shape Converter
~~~~~~~~~~~~~~~

.. automodule:: psd2svg.core.shape
   :members:
   :undoc-members:
   :show-inheritance:

Text Converter
~~~~~~~~~~~~~~

.. automodule:: psd2svg.core.text
   :members:
   :undoc-members:
   :show-inheritance:

Effects Converter
~~~~~~~~~~~~~~~~~

.. automodule:: psd2svg.core.effects
   :members:
   :undoc-members:
   :show-inheritance:

Adjustment Converter
~~~~~~~~~~~~~~~~~~~~

.. automodule:: psd2svg.core.adjustment
   :members:
   :undoc-members:
   :show-inheritance:

Paint Converter
~~~~~~~~~~~~~~~

.. automodule:: psd2svg.core.paint
   :members:
   :undoc-members:
   :show-inheritance:
