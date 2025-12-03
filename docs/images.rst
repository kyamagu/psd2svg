Image Handling
==============

This guide covers image embedding, external image export, and format selection for SVG output.

Overview
--------

psd2svg extracts raster image data from PSD layers when needed. For pixel-based layers (photos, rasterized content, smart objects), Photoshop stores raw pixel data within the PSD file. psd2svg retrieves this pixel data and includes it in the SVG output.

Note that layer effects (drop shadows, glows, etc.) are not part of the stored pixel data. They are converted to SVG filters separately. The extracted images represent the base layer content before any effects or filters are applied.

These extracted images can be:

* **Embedded** as base64-encoded data URIs within the SVG file
* **Exported** as external files referenced by the SVG

Embedded vs External Images
----------------------------

Embedded Images
~~~~~~~~~~~~~~~

By default, images are embedded as base64-encoded data URIs:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)

   # Save with embedded images (default)
   document.save("output.svg")

**Result:** All images are embedded within the SVG as ``data:image/...`` URIs.

**Pros:**

* Self-contained single file
* No external dependencies
* Works offline
* Easy to share and distribute

**Cons:**

* Larger file size (base64 adds ~33% overhead)
* Cannot leverage browser caching
* Difficult to update individual images

External Images
~~~~~~~~~~~~~~~

Export images to external files for better optimization:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)

   # Save with external images in same directory
   document.save("output.svg", image_prefix=".")
   # => output.svg, 01.webp, 02.webp, ...

   # Save with external images in subdirectory
   document.save("output.svg", image_prefix="images/img")
   # => output.svg, images/img01.webp, images/img02.webp, ...

**Result:** Images are saved as separate files and referenced by relative paths in the SVG.

**Pros:**

* Smaller SVG file size
* Images can be cached by browsers
* Easy to replace or update images
* Better for version control (text vs binary)

**Cons:**

* Multiple files to manage
* Requires proper directory structure
* External dependencies

**Command Line:**

.. code-block:: bash

   # Same directory as SVG
   psd2svg input.psd output.svg --image-prefix .

   # Subdirectory
   psd2svg input.psd output.svg --image-prefix images/img

Image Path Behavior
~~~~~~~~~~~~~~~~~~~

The ``image_prefix`` parameter is interpreted relative to the output SVG file's directory:

.. code-block:: python

   # If output.svg is in /path/to/output/file.svg
   document.save("/path/to/output/file.svg", image_prefix=".")
   # => Images in /path/to/output/ (same directory)

   document.save("/path/to/output/file.svg", image_prefix="images/img")
   # => Images in /path/to/output/images/ (subdirectory)

   document.save("/path/to/output/file.svg", image_prefix="../shared/img")
   # => Images in /path/to/shared/ (parent directory)

Image Formats
-------------

Supported Formats
~~~~~~~~~~~~~~~~~

psd2svg supports three image formats:

* **WebP** - Modern format with excellent compression (default)
* **PNG** - Lossless format with transparency support
* **JPEG** - Lossy format, best for photographs (no transparency)

WebP (Recommended)
~~~~~~~~~~~~~~~~~~

WebP provides the best compression while maintaining quality:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)

   # WebP is the default
   document.save("output.svg", image_prefix=".", image_format="webp")

**Pros:**

* Smallest file sizes (30-50% smaller than PNG)
* Supports transparency
* Good quality at lower bitrates
* Broad browser support (Chrome, Firefox, Safari, Edge)

**Cons:**

* Not supported in very old browsers (IE11, Safari <14)
* May require fallback for legacy support

**When to use:** Web delivery, modern applications, file size is a concern

PNG
~~~

PNG provides lossless compression with transparency:

.. code-block:: python

   document.save("output.svg", image_prefix=".", image_format="png")

**Pros:**

* Lossless compression
* Universal support (all browsers, viewers)
* Good for graphics with sharp edges
* Supports transparency

**Cons:**

* Larger file sizes than WebP
* Slower compression/decompression

**When to use:** Maximum compatibility, archival, print, lossless requirement

JPEG
~~~~

JPEG provides lossy compression for photographs:

.. code-block:: python

   document.save("output.svg", image_prefix=".", image_format="jpeg")

**Pros:**

* Excellent compression for photos
* Universal support
* Small file sizes for photographic content

**Cons:**

* Lossy compression (quality degradation)
* No transparency support (alpha channel discarded)
* Poor for graphics with sharp edges (artifacts)

**When to use:** Photographic content only, transparency not needed

**Command Line:**

.. code-block:: bash

   # WebP
   psd2svg input.psd output.svg --image-prefix . --image-format webp

   # PNG
   psd2svg input.psd output.svg --image-prefix . --image-format png

   # JPEG
   psd2svg input.psd output.svg --image-prefix . --image-format jpeg

Format Comparison
~~~~~~~~~~~~~~~~~

Example file sizes for a typical rasterized layer (1000x1000px with effects):

* **WebP:** 45 KB (lossy), 120 KB (lossless)
* **PNG:** 180 KB
* **JPEG:** 60 KB (no transparency)

Choose based on your requirements:

* **Best compression:** WebP lossy
* **Best quality:** PNG or WebP lossless
* **Best compatibility:** PNG
* **Photos only:** JPEG

Image Encoding Utilities
-------------------------

The ``image_utils`` module provides utilities for encoding images:

.. code-block:: python

   from psd2svg.image_utils import encode_image
   from PIL import Image

   # Load an image
   image = Image.open("photo.png")

   # Encode as base64 data URI
   data_uri = encode_image(image, format="webp")
   # => "data:image/webp;base64,UklGRiQAAABXRUJQVlA4..."

   # Use in SVG
   svg = f'<image href="{data_uri}" />'

**Supported Parameters:**

* ``format`` - Image format: "webp", "png", "jpeg" (default: "webp")
* ``quality`` - Quality for lossy formats (1-100, default: 95)
* ``lossless`` - Use lossless compression for WebP (default: False)

Example: Custom Quality
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg.image_utils import encode_image
   from PIL import Image

   image = Image.open("photo.png")

   # High quality WebP (95)
   high_quality = encode_image(image, format="webp", quality=95)

   # Lower quality WebP (75) for smaller size
   low_quality = encode_image(image, format="webp", quality=75)

   # Lossless WebP (larger but perfect quality)
   lossless = encode_image(image, format="webp", lossless=True)

Best Practices
--------------

Web Delivery
~~~~~~~~~~~~

For web applications, use external WebP images:

.. code-block:: python

   document.save(
       "output.svg",
       image_prefix="images/img",
       image_format="webp"
   )

**Benefits:**

* Smaller overall size
* Browser can cache images
* Faster initial page load

Offline/Email
~~~~~~~~~~~~~

For offline use or email, use embedded images:

.. code-block:: python

   document.save("output.svg")  # Embedded by default

**Benefits:**

* Single file
* No broken image links
* Works without network

Print/Archival
~~~~~~~~~~~~~~

For print or archival, use external PNG images:

.. code-block:: python

   document.save(
       "output.svg",
       image_prefix="images/img",
       image_format="png"
   )

**Benefits:**

* Lossless quality
* Universal compatibility
* Easy to manage and update

Performance Tips
----------------

Reduce File Size
~~~~~~~~~~~~~~~~

1. **Use WebP format** - 30-50% smaller than PNG
2. **External images** - Avoids base64 overhead
3. **Optimize quality** - Lower quality for acceptable results
4. **Minimize rasterization** - Simplify effects where possible

.. code-block:: python

   # Optimized for web
   document.save(
       "output.svg",
       image_prefix="images/img",
       image_format="webp"
   )

Improve Load Performance
~~~~~~~~~~~~~~~~~~~~~~~~~

For web applications:

1. **Use external images** - Enables browser caching
2. **Add image dimensions** - Prevents layout shift
3. **Lazy load images** - Load images as they enter viewport
4. **Use CDN** - Serve images from CDN for faster delivery

Working with Images
-------------------

The ``SVGDocument`` class provides access to extracted images through the ``images`` field:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)

   # Access images dictionary
   print(f"Number of images: {len(document.images)}")

   # Iterate through images
   for image_id, image in document.images.items():
       print(f"{image_id}: {image.size} {image.mode}")

**Image IDs:**

Images are keyed by auto-generated IDs (e.g., "image-1", "image-2", etc.) corresponding to the order they appear in the SVG.

Export and Load Images
~~~~~~~~~~~~~~~~~~~~~~~

Images can be exported and loaded separately:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   # Export document with images
   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage)
   data = document.export()

   # data = {
   #     "svg": "<svg>...</svg>",
   #     "images": {
   #         "image-1": b"...",  # Encoded image bytes
   #         "image-2": b"...",
   #     },
   #     "fonts": [...]
   # }

   # Load from exported data
   restored = SVGDocument.load(data["svg"], data["images"], data["fonts"])

This is useful for serialization or transferring documents between processes.

Troubleshooting
---------------

Images Not Appearing
~~~~~~~~~~~~~~~~~~~~

If images don't appear in the SVG:

1. **Check file paths** - Ensure external image files exist at the specified paths
2. **Verify relative paths** - Paths must be relative to the SVG file location
3. **Check file permissions** - Ensure image files are readable
4. **Validate SVG** - Use an XML validator to check for errors

Large File Sizes
~~~~~~~~~~~~~~~~

If file sizes are too large:

1. **Use external images** - Remove base64 overhead
2. **Switch to WebP** - 30-50% size reduction
3. **Lower quality** - Adjust quality parameter
4. **Minimize effects** - Simplify PSD effects to reduce rasterization

Poor Image Quality
~~~~~~~~~~~~~~~~~~

If image quality is poor:

1. **Increase quality** - Use higher quality setting (95-100)
2. **Use lossless** - Switch to PNG or lossless WebP
3. **Check source** - Verify PSD layer quality
4. **Use higher DPI** - If rasterizing at low resolution
