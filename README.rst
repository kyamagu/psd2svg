PSD2SVG
=======

PSD to SVG converter based on `psd-tools2`_ and `svgwrite`_.

.. image:: https://img.shields.io/pypi/v/psd2svg.svg
   :target: https://pypi.python.org/pypi/psd2svg
   :alt: PyPI Version

.. image:: https://img.shields.io/travis/kyamagu/psd2svg/master.svg
   :alt: Build Status
   :target: https://travis-ci.org/kyamagu/psd2svg

.. _`psd-tools2`: https://github.com/kyamagu/psd-tools

.. _`svgwrite`: https://github.com/mozman/svgwrite

Install
-------

Use ``pip`` to install::

    pip install psd2svg


Usage
-----

The package comes with a command-line tool::

    psd2svg input.psd output.svg

When the output path is a directory, or omitted, the tool infers the output
name from the input::

    psd2svg input.psd output/  # => output/input.svg
    psd2svg input.psd          # => input.svg

When ``--resource-path`` flag is specified, all png resources are exported
to the path specified by ``--resource-path``::

    psd2svg input.psd output.svg --resource-path .
    # => output.svg, xxx1.png, ...

    psd2svg input.psd output/ --resource-path .
    # => output/input.svg, output/xxx1.png, ...

    psd2svg input.psd output/ --resource-path=resources/
    # => output/input.svg, output/resources/xxx1.png, ...

    psd2svg input.psd svg/ --resource-path=../png/
    # => svg/input.svg, png/xxx1.png, ...


API
---

The package contains high-level conversion function ``psd2svg``:

.. code-block:: python

    from psd2svg import psd2svg

    # File IO.
    psd2svg('path/to/input.psd', 'path/to/output/')

    # Stream IO.
    with open('input.psd', 'rb') as fi:
        with open('output.svg', 'w') as fo:
            psd2svg(fi, fo)

    # psd_tools IO.
    from psd_tools import PSDImage
    psd = PSDImage.load('path/to/input.psd')
    svg = psd2svg(psd)
    print(svg)

    # Additionally, individual layers can be directly rendered.
    layer_svg = psd2svg(psd[3])
    print(layer_svg)


The package also has rasterizer module to convert SVG to PIL Image:


.. code-block:: python

    from psd2svg.rasterizer import create_rasterizer

    rasterizer = create_rasterizer()
    image = rasterizer.rasterize(svg)
    image.save('path/to/output.png')


The rasterizer requires one of Selenium + ChromeDriver, Apache Batik, or
Inkscape. Make sure to install them beforehand.


Test
----

Invoke tox::

    tox


Storage backend support
-----------------------

To use AWS S3 storage backend::

    pip install psd2svg[s3]

or::

    pip install boto3


The tool can specify URL instead of file path (S3 requires ``boto3``)::

    psd2svg http://example.com/input.psd
    psd2svg s3://bucketname/path/to/input.psd s3://bucketname/path/to/output/


To use HDFS storage backend::

  pip install psd2svg[hdfs,kerberos]

Notes
-----

* SVG 1.1 does not cover all the blending modes in Photoshop (e.g.,
  ``linear-dodge``)
* Filter effects are approximation. Some effects are not implemented.
* Most of adjustments layers are not implemented.
* Smart object filters are not implemented.
* Browser support: SVG rendering quality greatly differs depending on the
  browser. Chrome tends to be the best quality.
* APIs of this tool is NOT thread-safe.
* To use HDFS storage backend, Python 2.7 environment is needed
  and should be Kerberos-enabled and only read access is available.
