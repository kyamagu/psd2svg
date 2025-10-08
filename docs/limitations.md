# Limitations

This document describes limitations when converting PSD files to SVG, primarily due to fundamental differences between the SVG specification and Adobe Photoshop's rendering model, which follows [the PDF rendering specification](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf).

## Stroke on Raster Images

Adobe Photoshop can apply strokes around raster images, but SVG can only apply `stroke` attributes to geometric elements such as `<path>` or `<text>`.

To work around this limitation, the converter implements an SVG filter based on morphological operations to simulate the stroking effect. The following example demonstrates an `inner` stroke implementation:

```xml
<filter id="stroke_4">
  <feMorphology operator="erode" radius="1" in="SourceAlpha" />
  <feComposite operator="xor" in2="SourceAlpha" result="STROKEAREA" />
  <feFlood flood-color="#000000" flood-opacity="1" />
  <feComposite operator="in" in2="STROKEAREA" />
</filter>
```

However, this approach has significant limitations. The `<feMorphology>` element only supports rectangular filter shapes, which causes several issues:

- **Corner artifacts**: Square corners produce visual artifacts
- **Inconsistent width**: Stroke width varies depending on angle
- **Aliasing**: Lines lack smooth rendering due to missing anti-aliasing

A potential workaround would be to convert raster layers into path objects using vectorization techniques, which Adobe Photoshop likely employs during rendering.

## Stroke Alignment

SVG strokes do not support `inner` and `outer` alignment options. While the W3C has proposed a `stroke-alignment` attribute specification, it is not yet implemented in any web browsers or SVG renderers.

**Reference**: [SVG Strokes Specification](https://svgwg.org/specs/strokes/)
