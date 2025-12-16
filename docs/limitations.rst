Limitations
===========

While psd2svg strives to accurately convert PSD files to SVG format, there are inherent limitations due to differences between the Photoshop format and SVG capabilities.

Platform Support
----------------

Operating System Limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**All Platforms**: psd2svg works on Linux, macOS, and Windows with cross-platform text layer conversion support.

**Text Layer Conversion:**

* **Linux/macOS**: Full support with fontconfig for font resolution and file path discovery
* **Windows**: Full support with Windows registry for font resolution and file path discovery

**Font Resolution Strategy:**

psd2svg uses a hybrid font resolution approach:

1. **Static mapping**: ~4,950 fonts mapped by PostScript name

   * **539 default fonts**: Core fonts (Arial, Times New Roman, Noto fonts, Roboto, Adobe fonts, etc.)
   * **370 Hiragino variants**: Japanese fonts with W0-W9 weight pattern (generated dynamically)
   * **4,042 Morisawa fonts**: Professional Japanese typography fonts
   * Provides font family, style, and weight information
   * Works on all platforms without external dependencies
   * Enables text conversion to SVG ``<text>`` elements
   * JSON-based lazy loading for optimal performance

2. **Platform-specific font resolution** (Linux/macOS/Windows):

   * Queries system fonts when file paths needed
   * **Linux/macOS**: fontconfig with CharSet API
   * **Windows**: Windows registry + fontTools cmap parsing
   * Used automatically by ``FontInfo.find_with_files()`` method during conversion
   * Enables font embedding with ``embed_fonts=True``

**Font Embedding:**

Font embedding is fully supported on all platforms:

* **Static mapping**: Provides font metadata (family, style, weight) for text conversion
* **Font file discovery**: Uses platform-specific resolution to locate font files
* **Linux/macOS**: fontconfig with CharSet API (fontconfig-py >= 0.4.0)
* **Windows**: Windows registry + fontTools cmap parsing
* **Text conversion**: Works without font files (uses SVG ``<text>`` with font-family names)
* **Font embedding**: Automatically locates font files when ``embed_fonts=True``

**Custom Font Mapping:**

For fonts not in the default mapping (~4,950 fonts), provide custom mappings:

.. code-block:: python

   import json
   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   # Load custom font mapping
   with open("fonts.json") as f:
       custom_fonts = json.load(f)

   # Use in conversion
   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(psdimage, font_mapping=custom_fonts)

See the Font Handling guide for generating custom mappings.

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

Most adjustment layers are **not implemented**:

* Curves
* Levels
* Hue/Saturation
* Color Balance
* Brightness/Contrast
* Channel Mixer
* And others

**Experimental Support:**

* **Invert** adjustment layer is partially supported (experimental)

**Technical Limitations:**

Adjustment layers in Photoshop apply filters to the combined backdrop of all layers below them. SVG has fundamental architectural limitations that make this difficult to implement correctly:

* **CSS backdrop-filter**: Would be ideal but does not work on SVG elements (only HTML elements)
* **SVG BackgroundImage**: SVG filters' ``BackgroundImage`` feature has poor browser support and is not available in most rasterizers (including resvg)
* **Current workaround**: The experimental implementation wraps backdrop layers in a ``<symbol>`` and uses two ``<use>`` elements—one for the original backdrop and one with the filter applied

**Critical Limitation - Transparency Not Supported:**

The current implementation **does not work correctly when the backdrop has transparency**. Stacking two semi-transparent ``<use>`` elements produces incorrect visual results, as the layers are composited twice.

This means:

* **Opaque backdrops only**: Adjustment layers work reasonably well when all backdrop layers are fully opaque
* **Transparency breaks**: Any transparency in backdrop layers (layer opacity, transparent pixels, or blend modes) will render incorrectly
* **No clean solution**: Without native backdrop-filter support on SVG elements, there is no straightforward way to implement adjustment layers that handle transparency correctly

**Workaround:** Flatten adjustment layers in Photoshop before conversion, or export a flattened version. This is the recommended approach for production use.

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
* Manual kerning adjustments
* Tsume (East Asian character tightening)
* Ligatures (common ligatures and discretionary ligatures)
* Line height (leading)
* Horizontal and vertical text scaling
* Position, rotation, and scaling transformations
* **Arc warp effects** (experimental) - see Text Warp Effects below

**Unsupported Features:**

* Gradient fills and pattern strokes (solid colors only)
* Advanced OpenType features (e.g., stylistic sets, contextual alternates, positional forms)
* Variable fonts and font variations

**Text Warp Effects (Experimental):**

Text layers with arc warp effects are converted to SVG ``<textPath>`` elements that follow curved paths. This feature is experimental and automatically enabled when arc warp is detected.

**Supported Warp Types:**

* **Arc warp** (horizontal orientation only)

  * Positive values (+1 to +100): Arc bulging upward
  * Negative values (-1 to -100): Arc bulging downward
  * All intermediate warp values

**Not Yet Supported:**

* Vertical arc warp
* Other warp styles (Fish, Wave, Flag, etc.)
* Warp perspective transforms

**Technical Implementation:**

Arc-warped text uses SVG ``<textPath>`` with dynamically generated arc paths. The arc radius is calculated using trigonometry:

* ``scale = sin(π/2 × |warp_value|/100)``
* ``radius = (width + height) / 2 / scale``

For extreme warp values (|value| > 50), the ``textLength`` attribute is set to improve browser rendering consistency.

**Renderer Compatibility:**

* ✅ **Modern browsers**: Chrome, Firefox, Safari, Edge (good support)
* ✅ **PlaywrightRasterizer**: Full support via Chromium
* ⚠️ **ResvgRasterizer**: Basic support, but may have rendering differences
* ⚠️ **Vector editors**: Variable support (Inkscape, Sketch, Figma)

**Known Limitations:**

* Height adjustment uses half box height; should ideally use baseline height
* Only horizontal orientation supported
* Text wrapping with warp not yet implemented
* Unsupported warp styles fall back to straight line rendering

**Example:**

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   # Text with arc warp is automatically converted to textPath
   psdimage = PSDImage.open("curved_text.psd")
   document = SVGDocument.from_psd(psdimage)
   document.save("output.svg")

**Fallback:**

To disable text warp conversion and rasterize warped text instead:

.. code-block:: python

   document = SVGDocument.from_psd(psdimage, enable_text=False)

**Text Wrapping Support:**

Text wrapping for bounding box text (ShapeType=1) is supported using ``<foreignObject>`` with XHTML/CSS content. This feature is **opt-in** and disabled by default.

To enable text wrapping:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd2svg.core.text import TextWrappingMode
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")
   document = SVGDocument.from_psd(
       psdimage,
       text_wrapping_mode=TextWrappingMode.FOREIGN_OBJECT
   )

**foreignObject Renderer Compatibility:**

* ✅ **Supported**: Modern browsers (Chrome, Firefox, Safari, Edge)
* ✅ **Supported**: PlaywrightRasterizer (Chromium-based rasterizer)
* ❌ **Not supported**: ResvgRasterizer/resvg-py (the default rasterizer ignores foreignObject)
* ❌ **Not supported**: Many SVG tools (PDF converters, design tools like Inkscape/Sketch/Figma)

**Important Notes:**

* foreignObject text cannot be edited in vector graphics editors (appears as embedded HTML)
* Point text (ShapeType=0) always uses native SVG ``<text>`` elements, regardless of this setting
* Default behavior (``text_wrapping_mode=0``) maintains backward compatibility with native SVG text
* For web-only SVG display or browser-based rendering, foreignObject provides better text wrapping
* For maximum compatibility, leave text wrapping disabled (default)

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

**Text Scaling Limitation:**

Horizontal and vertical text scaling (``horizontal_scale`` and ``vertical_scale`` in PSD) uses ``transform`` on ``<tspan>`` elements, which is only supported in SVG 2.0. **No major browser currently supports this feature** (Chrome, Firefox, Safari, and Edge all ignore transforms on tspan elements).

**Impact:**

* Scaled text will not render correctly in any browser
* Text appears at normal size instead of scaled size
* A warning is logged during conversion

**Workarounds:**

1. **Recommended**: Use ``enable_text=False`` to rasterize text layers with scaling
2. Convert text to vector shapes (outlines) in Photoshop before conversion
3. Avoid using text scaling in your PSD designs

**Technical Background:**

While splitting scaled spans into separate ``<text>`` elements (which do support transforms in browsers) seems like a potential solution, this approach has fundamental issues:

* Line height calculations - scaled text affects vertical spacing in complex ways
* Transform combination - when layers have their own transforms, matrix multiplication is required
* Position calculations - would require knowing rendered text widths without a layout engine
* Missing attributes - parent attributes need careful propagation

Given these complexities, the current implementation emits a clear warning rather than attempting unreliable splitting.

**Letter Spacing Differences:**

Photoshop and SVG renderers may have slightly different default letter spacing and kerning behaviors:

* Photoshop uses optical kerning by default (AutoKern=true)
* SVG renderers use font's built-in kerning tables without optical adjustments
* Different text layout engines may have subtle spacing differences

To compensate for these differences, you can use the ``text_letter_spacing_offset`` parameter:

.. code-block:: python

   from psd2svg import SVGDocument
   from psd_tools import PSDImage

   psdimage = PSDImage.open("input.psd")

   # Apply a small negative offset to tighten letter spacing
   document = SVGDocument.from_psd(
       psdimage,
       text_letter_spacing_offset=-0.015
   )

   # Or use a positive offset to loosen spacing
   document = SVGDocument.from_psd(
       psdimage,
       text_letter_spacing_offset=0.01
   )

The offset is in pixels and is added to all letter-spacing values. Typical values range from -0.02 to 0.02. You may need to experiment with different values depending on your fonts and target renderers.

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
* All warp effects (arc, fish, wave, etc.) work correctly
* Custom transformations work correctly
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

Rasterizer Stability
---------------------

resvg-py Edge Cases
~~~~~~~~~~~~~~~~~~~

The bundled resvg rasterizer (via resvg-py) has stability issues with edge cases:

**Crashes (SIGABRT):**

The resvg-py library may crash instead of raising Python exceptions when encountering:

* Severely malformed or corrupted SVG content
* Missing SVG files (``from_file()`` with non-existent paths)
* Empty SVG documents (0x0 dimensions)

**Impact:**

These crashes cannot be caught with Python exception handling, which means:

* Applications may terminate unexpectedly
* Error recovery is not possible
* No proper error messages are available

**Workarounds:**

1. **Validate input** - Check file existence and parse SVG with XML parser before rasterizing
2. **Use PlaywrightRasterizer** - The optional browser-based rasterizer handles errors more gracefully
3. **Sanitize SVG** - Ensure SVG content is well-formed before rasterization

See the :doc:`rasterizers` documentation for detailed workarounds and examples.

**Status:** This is a limitation of the underlying resvg-py library, not psd2svg itself.

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
