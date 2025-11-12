PSD2SVG Documentation
=====================

PSD2SVG is a PSD to SVG converter based on `psd-tools <https://github.com/psd-tools/psd-tools>`_.

This tool converts Adobe Photoshop (PSD) files to Scalable Vector Graphics (SVG) format, preserving layers, effects, and vector shapes where possible.

.. image:: https://img.shields.io/pypi/v/psd2svg.svg
   :target: https://pypi.python.org/pypi/psd2svg
   :alt: PyPI Version

Features
--------

* Convert PSD files to SVG format
* Preserve layer structure and hierarchy
* Support for vector shapes, text layers, and effects
* Command-line interface and Python API
* Multiple rasterizer backends for SVG rendering
* Export images as embedded data URIs or external files

Quick Start
-----------

Install via pip:

.. code-block:: bash

   pip install psd2svg

Convert a PSD file:

.. code-block:: bash

   psd2svg input.psd output.svg

Use in Python:

.. code-block:: python

   from psd2svg import convert

   convert('input.psd', 'output.svg')

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   getting-started
   user-guide
   rasterizers
   limitations

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api-reference

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   development
   technical-notes
   changelog

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
