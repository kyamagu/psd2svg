Getting Started
===============

This guide will help you get started with psd2svg quickly.

Installation
------------

Install psd2svg using pip:

.. code-block:: bash

   pip install psd2svg

Requirements
~~~~~~~~~~~~

* Python 3.10 or higher
* Dependencies are automatically installed:

  * ``psd-tools`` - PSD file parsing
  * ``pillow`` - Image processing
  * ``numpy`` - Numerical operations
  * ``resvg-py`` - SVG rasterization

Command Line Usage
------------------

Basic Conversion
~~~~~~~~~~~~~~~~

The simplest way to convert a PSD file to SVG:

.. code-block:: bash

   psd2svg input.psd output.svg

Automatic Output Naming
~~~~~~~~~~~~~~~~~~~~~~~

When the output path is a directory or omitted, the tool infers the output name from the input:

.. code-block:: bash

   # Output to directory
   psd2svg input.psd output/
   # => output/input.svg

   # Output to current directory
   psd2svg input.psd
   # => input.svg

Command Line Options
~~~~~~~~~~~~~~~~~~~~

**Image handling:**

* ``--image-prefix PATH`` - Save extracted images to external files with this prefix, relative to the output SVG file's directory (default: embed images)
* ``--image-format FORMAT`` - Image format for rasterized layers: webp, png, jpeg (default: webp)

**Feature flags:**

* ``--no-text`` - Disable text layer conversion (rasterize text instead)
* ``--no-live-shapes`` - Disable live shape conversion (use paths instead of shape primitives)
* ``--no-title`` - Disable insertion of ``<title>`` elements with layer names

**Text adjustment:**

* ``--text-letter-spacing-offset OFFSET`` - Global offset (in pixels) to add to letter-spacing values (default: 0.0)

**Examples:**

.. code-block:: bash

   # Export images to same directory as SVG (using "." prefix)
   psd2svg input.psd output.svg --image-prefix .
   # => output.svg, 01.webp, 02.webp, ...

   # Export images to subdirectory (relative to SVG location)
   psd2svg input.psd output.svg --image-prefix images/img
   # => output.svg, images/img01.webp, images/img02.webp, ...

   # Export images as PNG
   psd2svg input.psd output.svg --image-prefix . --image-format png
   # => output.svg, 01.png, 02.png, ...

   # Export with nested output directory
   psd2svg input.psd output/result.svg --image-prefix .
   # => output/result.svg, output/01.webp, output/02.webp, ...

   # Disable text layer conversion
   psd2svg input.psd output.svg --no-text

   # Compact output: disable titles and use paths
   psd2svg input.psd output.svg --no-title --no-live-shapes

Python API - Quick Start
-------------------------

Simple Conversion Function
~~~~~~~~~~~~~~~~~~~~~~~~~~

For quick conversions, use the ``convert()`` function:

.. code-block:: python

   from psd2svg import convert

   # Convert with embedded images
   convert('input.psd', 'output.svg')

   # Convert with external images in same directory as SVG
   convert('input.psd', 'output.svg', image_prefix='.')
   # => output.svg, 01.webp, 02.webp, ...

   # Convert with external images in subdirectory (relative to output SVG)
   convert('input.psd', 'output.svg', image_prefix='images/img')
   # => output.svg, images/img01.webp, images/img02.webp, ...

   # Convert with external PNG images
   convert('input.psd', 'output.svg', image_prefix='images/img', image_format='png')
   # => output.svg, images/img01.png, images/img02.png, ...

   # Disable text layer conversion (rasterize text instead)
   convert('input.psd', 'output.svg', enable_text=False)

   # Disable live shapes (use paths instead)
   convert('input.psd', 'output.svg', enable_live_shapes=False)

   # Disable title elements and adjust letter spacing
   convert('input.psd', 'output.svg', enable_title=False, text_letter_spacing_offset=-0.015)

SVGDocument API
~~~~~~~~~~~~~~~

For more control over the conversion process, use the ``SVGDocument`` class:

.. code-block:: python

   from psd_tools import PSDImage
   from psd2svg import SVGDocument

   # Load PSD file
   psdimage = PSDImage.open("input.psd")

   # Create SVG document
   document = SVGDocument.from_psd(psdimage)

   # Save with embedded images
   document.save("output.svg", embed_images=True)

   # Get as string
   svg_string = document.tostring(embed_images=True)
   print(svg_string)

Next Steps
----------

* Read the :doc:`user-guide` for detailed usage examples
* Check the :doc:`api-reference` for complete API documentation
* Learn about :doc:`rasterizers` for rendering SVG to raster images
* Review :doc:`limitations` to understand current constraints
