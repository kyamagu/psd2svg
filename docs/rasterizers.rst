Rasterizers
===========

The psd2svg package uses resvg for converting SVG documents to raster images (PNG, JPEG, etc.).

Overview
--------

The rasterizer system provides a high-performance interface for converting SVG to PIL Image objects using the resvg rendering engine.

Resvg Rasterizer
----------------

Fast, accurate, and pure Rust implementation via resvg-py.

**Pros:**

* Fastest performance
* High accuracy
* No browser dependencies
* Simple installation
* Production-ready

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
