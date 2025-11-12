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

Factory Function
~~~~~~~~~~~~~~~~

.. autofunction:: psd2svg.rasterizer.create_rasterizer

Base Rasterizer
~~~~~~~~~~~~~~~

.. autoclass:: psd2svg.rasterizer.BaseRasterizer
   :members:
   :undoc-members:
   :show-inheritance:

Rasterizer Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The specific rasterizer implementations (ResvgRasterizer, ChromiumRasterizer, BatikRasterizer, InkscapeRasterizer)
are not directly exposed in the public API. Use the ``create_rasterizer()`` factory function to instantiate them.

Example:

.. code-block:: python

   from psd2svg.rasterizer import create_rasterizer

   # Creates an instance of ResvgRasterizer
   rasterizer = create_rasterizer('resvg')

   # Creates an instance of ChromiumRasterizer
   rasterizer = create_rasterizer('chromium')

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

Type Converter
~~~~~~~~~~~~~~

.. automodule:: psd2svg.core.type
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
