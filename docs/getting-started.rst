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

External Image Resources
~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``--images-path`` flag to export PNG resources to external files:

.. code-block:: bash

   # Export images to current directory
   psd2svg input.psd output.svg --images-path .
   # => output.svg, xxx1.png, xxx2.png, ...

   # Export images to specific directory
   psd2svg input.psd output/ --images-path resources/
   # => output/input.svg, output/resources/xxx1.png, ...

   # Export images to parent directory
   psd2svg input.psd svg/ --images-path=../png/
   # => svg/input.svg, png/xxx1.png, ...

Python API - Quick Start
-------------------------

Simple Conversion Function
~~~~~~~~~~~~~~~~~~~~~~~~~~

For quick conversions, use the ``convert()`` function:

.. code-block:: python

   from psd2svg import convert

   # Convert with embedded images
   convert('input.psd', 'output.svg')

   # Convert with external images
   convert('input.psd', 'output.svg', image_prefix='images/img_')
   # => output.svg, images/img_01.webp, images/img_02.webp, ...

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
