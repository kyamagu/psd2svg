# Clipping conversion

Clipping involves non-trivial conversion. The basic approach is to use `<clipPath>` or `<mask>` SVG elements, but Photoshop can have arbitrarily complex rendering procedures due to the presence of vector drawings or filter effects.

## Basic idea

Consider the following case:

```
  [1] ShapeLayer('Star 1' size=30x29)
  [2] +TypeLayer('B' size=22x23 clip)
```

This can be translated to the following SVG structure:

```xml
<path id="path0" d="M15,14.5 ..." />
<clipPath id="clip0">
  <use href="#path0" />
</clipPath>
<text clip-path="url(#clip0)">B</text>
```

If the clipping base is not a shape layer, we can instead use a mask.

```
  [1] PixelLayer('Star 1' size=30x29)
  [2] +TypeLayer('B' size=22x23 clip)
```

```xml
<image id="image0" href="pixel.png">
<mask id="mask0" mask-type="alpha">
  <use href="image0" />
</mask>
<text mask="url(#mask0)">B</text>
```

This structure is the most basic form of translation.

### Styling SVG use element

In SVG, the `<use>` element does not allow overriding the `fill` or `stroke` attributes of the referenced element. Therefore, in the following example, `fill="transparent"` is ignored.

```xml
<path id="path0" d="M15,14.5 ..." fill="red" />
<clipPath id="clip0">
  <use href="#path0" />
</clipPath>
<use href="#path0" fill="transparent" stroke="black" />
```

To correctly apply drawing attributes, we instead need to do the following: prepare a plain `<path>` element (like a `<symbol>`), then reference this element in the `<use>` element with the desired attributes.

```xml
<clipPath id="clip0">
  <path id="path0" d="M15,14.5 ..."/>
</clipPath>
<use href="#path0" fill="red" />
<use href="#path0" fill="transparent" stroke="black" />
```

### Stroke after clipping layers

In Photoshop, stroke (both as a shape attribute and as a filter effect) is applied after all clipping layers are rendered.
Consider the following example, where the first shape layer has both fill and stroke attributes enabled:

```
  [1] ShapeLayer('Star 1' size=30x29)
  [2] +TypeLayer('B' size=22x23 clip)
  [3] +TypeLayer('C' size=22x23 clip)
```

This translates to the following.

```xml
<clipPath id="clip0">
  <path id="path0" d="M15,14.5 ..."/>
</clipPath>
<use href="#path0" fill="red" />
<text clip-path="url(#clip0)">B</text>
<text clip-path="url(#clip0)">C</text>
<use href="#path0" fill="transparent" stroke="black" />
```

Or, we can group clipping layers:

```xml
<clipPath id="clip0">
  <path id="path0" d="M15,14.5 ..."/>
</clipPath>
<use href="#path0" fill="red" />
<g clip-path="url(#clip0)">
  <text>B</text>
  <text>C</text>
</g>
<use href="#path0" fill="transparent" stroke="black" />
```

There are filter effects that happen before (e.g., filling) or after (e.g., stroking) the rendering of the clipped layers.

### Stroke effect on raster layers

Photoshop can apply stroke effects to any layer, whereas SVG allows stroke only on shape or text elements. We have to emulate the stroke effect using filter effects. The following example emulates a stroke effect on a pixel layer:

```xml
<mask id="mask0" mask-type="alpha">
  <image id="image0" href="pixel.png">
</mask>
<use href="image0" />
<text mask="url(#mask0)">B</text>
<use href="image0" filter="url(#stroke0)">
<filter id="stroke0">
  <feMorphology operator="dilate" radius="1" in="SourceAlpha" result="thicken" />
  <feComposite operator="out" in="thicken" in2="SourceGraphic" />
</filter>
```

The SVG filter configuration depends on the stroke properties (alignment and stroke width).

### Regular masks and clipping masks

When a clipped layer has a mask, we have to group the clipping layers and apply the mask to the group.

```xml
<mask id="mask0" mask-type="alpha">
  <image id="image0" href="pixel.png">
</mask>
<use href="image0" />
<g mask="url(#mask0)">
  <mask id="mask1" mask-type="alpha">
    <image />
  </mask>
  <text mask="url(#mask1)">B</text>
</g>
<use href="image0" filter="url(#stroke0)">
<filter id="stroke0">
  <feMorphology operator="dilate" radius="1" in="SourceAlpha" result="thicken" />
  <feComposite operator="out" in="thicken" in2="SourceGraphic" />
</filter>
```

### Wrapping up

Depending on the target layer kind, we have the following structure for clipping layers.

Drawing target:

```xml
<!-- clip path -->
<clipPath id="clipPath0">
  <path id="path0" />
</clipPath>
<!-- bottom effects like fill -->
<use href="#path0" fill="red" />
<!-- clipped layers -->
<g clip-path="url(#clipPath0)"></g>
<!-- top effects like stroke -->
<use href="#path0" fill="transparent" stroke="black" />
```

Raster target:

```xml
<!-- clip mask -->
<mask id="mask0">
  <image id="image0" />
</mask>
<!-- bottom effects like fill -->
<use href="#image0" />
<!-- clipped layers -->
<g mask="url(#mask0)"></g>
<!-- top effects like stroke -->
<use href="#image0" filter="url(#filter0)" />
<filter id="filter0"></filter>
```

## Conversion

The requirement to implement the above conversion is the following two logic.

1. Beginning of the clip section (mask or clipPath creation, fill, group)
2. End of the clip section (stroke)

This would be translated to the following conversion loop structure.

```python
for layer in psdimage:
    if layer.has_clip_layers():
        self.add_clip_target_begin(layer)
        for clip_layer in layer.clip_layers:
            self.add_layer(clip_layer)
        self.add_clip_target_end(layer)
    elif layer.clipping_layer:
        pass  # Skip clipping layers
    else:
        self.add_layer(layer)
```