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

Example:

.. code-block:: python

   from psd2svg.rasterizer import ResvgRasterizer

   # Create rasterizer instance
   rasterizer = ResvgRasterizer(dpi=96)

   # Rasterize from string
   image = rasterizer.from_string(svg_string)

   # Rasterize from file
   image = rasterizer.from_file('input.svg')

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
