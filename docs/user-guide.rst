User Guide
==========

This guide provides detailed information about using psd2svg for converting PSD files to SVG format.

SVGDocument Class
-----------------

The ``SVGDocument`` class is the main interface for working with SVG documents and their resources.

Creating SVGDocument
~~~~~~~~~~~~~~~~~~~~

From PSD File
^^^^^^^^^^^^^

.. code-block:: python

   from psd_tools import PSDImage
   from psd2svg import SVGDocument

   # Load PSD
   psdimage = PSDImage.open("input.psd")

   # Create SVG document
   document = SVGDocument.from_psd(psdimage)

   # Create with custom letter spacing offset
   document = SVGDocument.from_psd(
       psdimage,
       text_letter_spacing_offset=-0.015
   )

Saving SVG Documents
~~~~~~~~~~~~~~~~~~~~

With Embedded Images
^^^^^^^^^^^^^^^^^^^^

Embed all images as base64-encoded data URIs within the SVG file:

.. code-block:: python

   document.save("output.svg", embed_images=True)

With External Images
^^^^^^^^^^^^^^^^^^^^

Export images to external files:

.. code-block:: python

   # Export as PNG
   document.save("output.svg", image_prefix="images/img_", image_format="png")
   # => output.svg, images/img_01.png, images/img_02.png, ...

   # Export as WebP
   document.save("output.svg", image_prefix="images/img_", image_format="webp")
   # => output.svg, images/img_01.webp, images/img_02.webp, ...

   # Export as JPEG
   document.save("output.svg", image_prefix="images/img_", image_format="jpeg")
   # => output.svg, images/img_01.jpg, images/img_02.jpg, ...

Getting SVG as String
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # With embedded images
   svg_string = document.tostring(embed_images=True)

   # With external image references
   svg_string = document.tostring(image_prefix="img_", image_format="png")

Export and Load
~~~~~~~~~~~~~~~

Export the document to a dictionary format:

.. code-block:: python

   # Export
   exported = document.export()
   # Returns: {"svg": "<svg>...</svg>", "images": {"id1": <PIL.Image>, ...}}

   # Load back
   document = SVGDocument.load(exported["svg"], exported["images"])

This is useful for serialization or transferring documents between processes.

Rasterization
-------------

Convert SVG documents to raster images using the built-in rasterizer support.

Using Built-in Method
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg import SVGDocument

   document = SVGDocument.from_psd(psdimage)

   # Rasterize using default settings
   image = document.rasterize()
   image.save('output.png')

   # Rasterize with custom DPI
   image = document.rasterize(dpi=300)  # High resolution
   image.save('output_high_res.png')

Using Rasterizer Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer

   # Create rasterizer instance
   rasterizer = ResvgRasterizer(dpi=96)

   # Rasterize from string
   svg_string = document.tostring(embed_images=True)
   image = rasterizer.from_string(svg_string)
   image.save('output.png')

   # Rasterize from file
   image = rasterizer.from_file('input.svg')

The Rasterizer
~~~~~~~~~~~~~~

psd2svg uses **resvg** for rasterization, which provides fast and accurate rendering
with no external dependencies beyond the resvg-py Python package.

See :doc:`rasterizers` for detailed documentation and examples.

The convert() Function
----------------------

For simple one-step conversions, use the ``convert()`` convenience function:

.. code-block:: python

   from psd2svg import convert

   # Basic conversion with embedded images
   convert('input.psd', 'output.svg')

   # With external images
   convert('input.psd', 'output.svg', image_prefix='images/img_')

   # With custom image format
   convert('input.psd', 'output.svg',
           image_prefix='images/img_',
           image_format='webp')

   # With custom letter spacing offset
   convert('input.psd', 'output.svg',
           text_letter_spacing_offset=-0.015)

Parameters
~~~~~~~~~~

* ``input_path`` (str): Path to input PSD file
* ``output_path`` (str): Path to output SVG file
* ``embed_images`` (bool): Whether to embed images as data URIs (default: True if no image_prefix)
* ``image_prefix`` (str, optional): Prefix for external image files
* ``image_format`` (str): Image format - 'png', 'jpeg', or 'webp' (default: 'webp')
* ``text_letter_spacing_offset`` (float): Global offset (in pixels) to add to all letter-spacing values (default: 0.0)

Working with Images
-------------------

Image Encoding
~~~~~~~~~~~~~~

The ``image_utils`` module provides utilities for encoding images:

.. code-block:: python

   from psd2svg.image_utils import encode_image_to_base64
   from PIL import Image

   # Load an image
   image = Image.open("photo.png")

   # Encode as base64 data URI
   data_uri = encode_image_to_base64(image, format='png')
   # => "data:image/png;base64,iVBORw0KG..."

Image Formats
~~~~~~~~~~~~~

Supported image formats for export:

* **PNG** - Lossless, supports transparency, larger file size
* **WebP** - Modern format, good compression, supports transparency
* **JPEG** - Lossy, smaller file size, no transparency

Choose based on your needs:

* Use PNG for images requiring transparency or lossless quality
* Use WebP for modern web applications with good compression
* Use JPEG for photographs where small file size is important

Best Practices
--------------

Performance Tips
~~~~~~~~~~~~~~~~

1. **Use external images for large PSDs**: Embedding many large images can create huge SVG files
2. **Choose WebP format**: Provides good quality with smaller file sizes
3. **Use appropriate DPI**: Default DPI (96) is suitable for screen display, use 300+ for print

Quality Considerations
~~~~~~~~~~~~~~~~~~~~~~

1. **SVG limitations**: Some Photoshop effects and blending modes aren't supported in SVG 1.1
2. **Browser compatibility**: Chrome provides best SVG rendering quality
3. **Test output**: Always verify the output in your target browser/application

Thread Safety
~~~~~~~~~~~~~

**Important**: The psd2svg API is NOT thread-safe. Do not share ``SVGDocument`` instances across threads.

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from psd_tools import PSDImage
   from psd2svg import SVGDocument

   try:
       psdimage = PSDImage.open("input.psd")
       document = SVGDocument.from_psd(psdimage)
       document.save("output.svg")
   except FileNotFoundError:
       print("PSD file not found")
   except Exception as e:
       print(f"Conversion failed: {e}")
