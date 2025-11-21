Limitations
===========

While psd2svg strives to accurately convert PSD files to SVG format, there are inherent limitations due to differences between the Photoshop format and SVG capabilities.

SVG 1.1 Limitations
-------------------

Blending Modes
~~~~~~~~~~~~~~

SVG 1.1 does not support all Photoshop blending modes. Some blending modes have no SVG equivalent:

**Unsupported blending modes:**

* Dissolve
* Darker Color
* Lighter Color
* Linear Dodge
* Linear Burn
* Vivid Light
* Linear Light
* Pin Light
* Hard Mix
* Subtract
* Divide

Linear Dodge is converted to ``plus-darker`` and Linear Burn to ``plus-lighter``.
However, majority of SVG renderers do not support these modes.

**Partially supported:**

Some blending modes may render differently across browsers or may use approximations.

**Workaround:** Consider flattening layers with unsupported blending modes in Photoshop before conversion.

Gradient
--------

SVG does not support all the gradient types available in Photoshop:

* Angle
* Reflected
* Diamond

Also, gradient interpolation methods may differ. Classic interpolation is closest to SVG's linear interpolation, but others may not match exactly:

* Perceptual
* Linear
* Classic
* Smooth
* Stripes

**Workaround:** Use linear or radial gradients in Photoshop for best compatibility.

Filter Effects
--------------

The following filter effects are not supported:

* Bevels and embossing
* Satin

Other filter effects are approximations and may not exactly match Photoshop's rendering:

* Drop shadows and inner shadows
* Inner and outer glows
* Stroke
* Color, gradient, and pattern overlays

The converter does its best to approximate these effects, but results may vary.

Adjustment Layers
-----------------

Adjustment layers are **not implemented**:

* Curves
* Levels
* Hue/Saturation
* Color Balance
* Brightness/Contrast
* Channel Mixer
* And others

**Workaround:** Flatten adjustment layers in Photoshop before conversion, or export a flattened version.

Smart Objects
-------------

Smart Object Features
~~~~~~~~~~~~~~~~~~~~~

* **Smart Object filters**: Not supported
* **Embedded smart objects**: Limited support
* **Linked smart objects**: Not supported

**Workaround:** Rasterize smart objects in Photoshop before conversion if they contain unsupported features.

Text Layers
-----------

Text layers can be converted to SVG ``<text>`` elements (``enable_text=True``, default) or rasterized as images (``enable_text=False``).

**Note:** Text conversion is experimental and has limitations. For production use, test thoroughly with your target SVG renderers.

Native SVG Text Conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When ``enable_text=True`` (default), text layers are converted to native SVG ``<text>`` elements.

**Supported Features:**

* Text content with multiple paragraphs and styled spans
* Font family, size, weight (bold), and style (italic)
* Faux bold and faux italic
* Font color (solid fill and stroke colors)
* Horizontal and vertical writing modes
* Text alignment (left, center, right, justify)
* Text decoration (underline, strikethrough)
* Text transformation (all-caps, small-caps)
* Superscript and subscript with accurate positioning
* Baseline shift for custom vertical positioning
* Letter spacing (tracking)
* Line height (leading)
* Horizontal and vertical text scaling
* Position, rotation, and scaling transformations

**Unsupported Features:**

* Text wrapping for bounding box text
* Gradient fills and pattern strokes
* Kerning and ligatures
* OpenType features
* Variable fonts and font variations

**Font Requirements:**

Text conversion requires fonts to be installed on the system. The converter uses ``fontconfig`` to resolve font names. If a font is not found:

* A warning is logged
* Text may fall back to a default system font
* Results may differ from Photoshop's rendering

Cross-platform font availability varies—test on your target deployment environment.

**SVG Renderer Compatibility:**

Rendering quality varies significantly across SVG renderers:

* **Chromium-based browsers** (Chrome, Edge): Best support, including vertical text features
* **Firefox**: Good support with minor differences
* **Safari**: Acceptable support with some limitations
* **resvg** (bundled rasterizer): Does not support:

  * ``text-orientation: upright`` for vertical writing mode
  * ``dominant-baseline`` alignment for vertical text
  * ``transform`` on ``<tspan>`` elements (SVG 1.1 limitation for horizontal/vertical scaling)

For best results with vertical text, use Chromium-based browsers for viewing or rendering.

**Note on Text Scaling:** Horizontal and vertical text scaling uses ``transform`` on ``<tspan>`` elements, which is an SVG 2.0 feature. While most modern browsers support this, some older SVG 1.1 renderers may not render scaled text correctly.

Rasterized Text (Image Fallback)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When ``enable_text=False``, the converter uses the rasterized preview image embedded in the PSD file.

This means:

* **Text is not editable** in the resulting SVG
* **Text is not selectable** or searchable
* **Scaling may reduce quality** since text becomes a raster image
* **File size increases** with embedded raster text

Since text is rasterized:

* Text appears exactly as rendered in Photoshop, including all effects
* Complex text effects (gradients, strokes, shadows) are preserved
* Warped text and custom transformations work correctly
* No font installation required on the target system

**Workarounds:**

* If you need **editable/scalable text**: Convert text to vector shapes (outlines) in Photoshop before conversion
* If you need **smaller file sizes**: Use external image export instead of embedded images
* If text quality is critical: Export at higher DPI or use the rasterizer with appropriate scaling

3D and Special Features
------------------------

The following Photoshop features are not supported:

* 3D layers
* Video layers
* Animation timeline
* Actions and scripts
* Layer comps (only the active comp is converted)

Browser Compatibility
---------------------

SVG Rendering Differences
~~~~~~~~~~~~~~~~~~~~~~~~~~

SVG rendering quality varies significantly across browsers:

**Best to Worst:**

1. **Chrome/Chromium**: Most accurate and feature-complete
2. **Firefox**: Good support, minor differences
3. **Safari**: Acceptable, some edge cases
4. **Edge**: Generally good (Chromium-based)

**Recommendation:** Test your SVG output in target browsers to ensure acceptable quality.

Known Issues
~~~~~~~~~~~~

* Filter effects may render differently in different browsers
* Some color profiles may not be preserved
* Complex gradients may have slight variations

Performance Considerations
--------------------------

Large Files
~~~~~~~~~~~

* **Complex PSDs**: Large files with many layers may result in large SVG files
* **Many embedded images**: Embedding images as data URIs increases file size significantly
* **Processing time**: Complex documents may take time to convert

**Workaround:**

* Use external images instead of embedding: ``convert('in.psd', 'out.svg', image_prefix='img_')``
* Simplify layer structure in Photoshop when possible
* Merge similar layers

Memory Usage
~~~~~~~~~~~~

* Large PSD files require significant memory to process
* Multiple concurrent conversions may exhaust memory

Thread Safety
-------------

**IMPORTANT**: The psd2svg API is **NOT thread-safe**.

* Do not share ``SVGDocument`` instances across threads
* Do not perform concurrent operations on the same document
* Use separate instances for parallel processing

Color Management
----------------

Color Space Limitations
~~~~~~~~~~~~~~~~~~~~~~~

* **CMYK**: May not convert accurately to RGB
* **Lab color**: Not supported
* **Color profiles**: May not be fully preserved
* **Spot colors**: Not supported

**Workaround:** Convert to RGB in Photoshop before conversion for best results.

Precision
~~~~~~~~~

Some color values may have minor precision differences due to format conversions.

Vector Shapes
-------------

Shape Limitations
~~~~~~~~~~~~~~~~~

* Some custom shape tools may not translate perfectly
* Vector masks have limitations

**Workaround:** Simplify paths in Photoshop if conversion issues occur.

Known Workarounds
-----------------

For Best Results
~~~~~~~~~~~~~~~~

1. **Simplify layer structure**: Merge unnecessary layers
2. **Flatten effects**: Rasterize complex effects
3. **Use RGB color mode**: Convert from CMYK if needed
4. **Rasterize smart objects**: If they contain unsupported features
5. **Test output**: Always verify SVG output in target environment
6. **Use external images**: For large PSDs with many raster elements

For Production Use
~~~~~~~~~~~~~~~~~~

1. **Pre-process PSDs**: Create conversion-friendly versions
2. **Automate testing**: Test converted SVGs in target browsers
3. **Fallback strategy**: Keep rasterized versions as fallback
4. **Version control**: Track both PSD and SVG versions

Reporting Issues
----------------

If you encounter issues not listed here:

1. Check if it's a known limitation
2. Test with simplified PSD files
3. Report issues at: https://github.com/kyamagu/psd2svg/issues

Include:

* PSD file characteristics (size, layers, features used)
* Error messages or unexpected behavior
* Expected vs. actual output
* Environment details (Python version, OS)
