# Overlay Filter Effects

Overlay effects can be thought of as adding another element on top of the original.

```xml
<image id="image_0" />
<use href="#image_0" filter="url(#filter_0)" class="color_overlay" />
<use href="#image_0" filter="url(#filter_1)" class="color_overlay" />
<filter id="filter_0">
  <feFlood flood-color="green" flood-alpha="0.5" result="flood" />
  <feComposite in="SourceAlpha" in2="flood" operator="in" />
</filter>
<filter id="filter_1">
  <feFlood flood-color="red" flood-alpha="0.5" result="flood" />
  <feComposite in="SourceAlpha" in2="flood" operator="in" />
</filter>
```

For simple overlays, this is equivalent to using a mask with fill.

```xml
<mask id="mask_0" mask-type="alpha">
  <image id="image_0">
</mask>
<use href="#image_0">
<rect color="green" alpha="0.5" mask="url(#mask_0)">
<rect color="red" alpha="0.5" mask="url(#mask_0)">
```

## Stroke

Things get complicated when there is a stroke, because the overlay must be applied before the stroke.

```xml
<rect id="rect_0" />
<use href="#rect_0" fill="gray" />  <!-- fill -->
<use href="#rect_0" filter="url(#filter_0)" class="color_overlay" />
<filter id="filter_1">
  <feFlood flood-color="red" flood-alpha="0.5" result="flood" />
  <feComposite in="SourceAlpha" in2="flood" operator="in" />
</filter>
<use href="#rect_0" fill="transparent" stroke="black" />  <!-- stroke -->
```

The above is equivalent to applying fill operations on geometric elements (shapes and text).

```xml
<defs>
  <rect id="rect_0" />
</defs>
<use href="#rect_0" fill="gray" />  <!-- fill -->
<use href="#rect_0" fill="red" opacity="0.5" class="color_overlay" />
<use href="#rect_0" fill="transparent" stroke="black" />  <!-- stroke -->
```

Interpreting overlay effects as clipped fill layers would likely be easier to implement.

```xml
<clipPath id="clip_0">
  <rect id="rect_0" />
</clipPath>
<use href="#rect_0" fill="gray" />
<g clip-path="url(#clip_0)">
    <use href="#rect_0" fill="red" opacity="0.5" class="color_overlay" />
</g>
<use href="#rect_0" fill="transparent" stroke="black" />
```

In any case, the generic rendering procedure for a single layer could be the following:

1. Shape definition; e.g., `<clipPath>`, `<mask>`, `<defs>`
2. Fill
3. Clipping or filter effects for color
4. Stroke
