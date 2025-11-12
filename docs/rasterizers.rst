Rasterizers
===========

Rasterizers convert SVG documents to raster images (PNG, JPEG, etc.). The psd2svg package supports multiple rasterizer backends.

Overview
--------

The rasterizer system provides a unified interface for converting SVG to PIL Image objects using different rendering engines.

Available Rasterizers
---------------------

resvg (Recommended)
~~~~~~~~~~~~~~~~~~~

Fast, accurate, and pure Rust implementation.

**Pros:**

* Fastest performance
* High accuracy
* No browser dependencies
* Integrated via ``resvg-py``

**Installation:**

The ``resvg-py`` package is included as a dependency, so no additional installation is needed.

**Usage:**

.. code-block:: python

   from psd2svg.rasterizer import create_rasterizer

   rasterizer = create_rasterizer('resvg')
   image = rasterizer.rasterize('input.svg')
   image.save('output.png')

Chromium
~~~~~~~~

Uses Chrome or Chromium browser for rendering.

**Pros:**

* High-quality rendering
* Good standards compliance
* Handles complex SVG features

**Cons:**

* Requires browser installation
* Slower than resvg
* Requires Selenium WebDriver

**Installation:**

.. code-block:: bash

   # Install Selenium
   pip install selenium

   # Install ChromeDriver (or use webdriver-manager)
   pip install webdriver-manager

**Usage:**

.. code-block:: python

   from psd2svg.rasterizer import create_rasterizer

   rasterizer = create_rasterizer('chromium')
   image = rasterizer.rasterize('input.svg')
   image.save('output.png')

Batik
~~~~~

Apache Batik SVG toolkit (Java-based).

**Pros:**

* Mature and stable
* Good SVG support

**Cons:**

* Requires Java installation
* Slower performance
* External dependency

**Installation:**

1. Download Apache Batik from https://xmlgraphics.apache.org/batik/
2. Extract and set ``BATIK_PATH`` environment variable

**Usage:**

.. code-block:: python

   import os

   # Set Batik path
   os.environ['BATIK_PATH'] = '/path/to/batik'

   from psd2svg.rasterizer import create_rasterizer

   rasterizer = create_rasterizer('batik')
   image = rasterizer.rasterize('input.svg')
   image.save('output.png')

Inkscape
~~~~~~~~

Inkscape command-line tool.

**Pros:**

* Excellent SVG support
* Widely available

**Cons:**

* Requires Inkscape installation
* Slower performance
* Command-line overhead

**Installation:**

Download and install Inkscape from https://inkscape.org/

**Usage:**

.. code-block:: python

   from psd2svg.rasterizer import create_rasterizer

   rasterizer = create_rasterizer('inkscape')
   image = rasterizer.rasterize('input.svg')
   image.save('output.png')

Using Rasterizers
-----------------

Factory Function
~~~~~~~~~~~~~~~~

The ``create_rasterizer()`` function creates rasterizer instances:

.. code-block:: python

   from psd2svg.rasterizer import create_rasterizer

   # Create by name
   rasterizer = create_rasterizer('resvg')
   rasterizer = create_rasterizer('chromium')
   rasterizer = create_rasterizer('batik')
   rasterizer = create_rasterizer('inkscape')

Rasterizing from File
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg.rasterizer import create_rasterizer

   rasterizer = create_rasterizer('resvg')

   # Basic rasterization
   image = rasterizer.rasterize('input.svg')
   image.save('output.png')

   # With custom dimensions
   image = rasterizer.rasterize('input.svg', width=800, height=600)

   # With scale factor
   image = rasterizer.rasterize('input.svg', scale=2.0)

Rasterizing from String
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from psd2svg import SVGDocument
   from psd2svg.rasterizer import create_rasterizer

   # Get SVG as string
   document = SVGDocument.from_psd(psdimage)
   svg_string = document.tostring(embed_images=True)

   # Rasterize
   rasterizer = create_rasterizer('resvg')
   image = rasterizer.rasterize_from_string(svg_string)
   image.save('output.png')

Direct Method on SVGDocument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``SVGDocument`` class has a built-in ``rasterize()`` method that uses resvg by default:

.. code-block:: python

   from psd2svg import SVGDocument

   document = SVGDocument.from_psd(psdimage)

   # Uses resvg by default
   image = document.rasterize()
   image.save('output.png')

   # With parameters
   image = document.rasterize(width=1920, height=1080)

Custom Rasterizer Implementation
---------------------------------

You can create custom rasterizers by inheriting from ``BaseRasterizer``:

.. code-block:: python

   from psd2svg.rasterizer.base_rasterizer import BaseRasterizer
   from PIL import Image

   class MyRasterizer(BaseRasterizer):
       def rasterize_from_string(
           self,
           svg_string: str,
           width: int | None = None,
           height: int | None = None,
           scale: float = 1.0,
       ) -> Image.Image:
           # Implement your rendering logic
           pass

Performance Comparison
----------------------

Approximate relative performance (smaller is faster):

1. **resvg**: 1x (baseline, fastest)
2. **chromium**: 5-10x slower
3. **batik**: 3-8x slower
4. **inkscape**: 8-15x slower

Recommendation: Use **resvg** for production use unless you have specific requirements that necessitate another backend.

Troubleshooting
---------------

resvg Issues
~~~~~~~~~~~~

If resvg fails to install:

.. code-block:: bash

   # Make sure you have a compatible Python version
   python --version  # Should be 3.10-3.14

   # Try upgrading pip
   pip install --upgrade pip

   # Install resvg-py
   pip install resvg-py

Chromium Issues
~~~~~~~~~~~~~~~

If Chromium rasterizer fails:

1. Ensure ChromeDriver is installed and in PATH
2. Check Chrome/Chromium version compatibility
3. Try using ``webdriver-manager`` for automatic driver management

.. code-block:: bash

   pip install webdriver-manager

Batik Issues
~~~~~~~~~~~~

If Batik fails to run:

1. Verify Java is installed: ``java -version``
2. Check ``BATIK_PATH`` environment variable
3. Ensure Batik JAR files are accessible

Inkscape Issues
~~~~~~~~~~~~~~~

If Inkscape fails:

1. Verify Inkscape is installed: ``inkscape --version``
2. Ensure Inkscape is in system PATH
3. Check file permissions
