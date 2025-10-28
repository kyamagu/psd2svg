# Shape operations

Photoshop supports boolean operation for path objects. SVG does not natively support path operations, but it is possible to reproduce path operations using `<mask>`.

The basics are:

- AND operation is a chain of `<mask>`.
- OR operation simply places multiple shape elements inside the same mask container.
- NOT operation is a black fill.

Unfortunately, strokes do not render correctly. Using `<clipPath>` might render strokes, but `<clipPath>` does not support NOT operator unless `<path>` element is used with `evenodd` rule.

## Union (OR)

A naive approach is to render multiple shapes in order.

```xml
<g>
  <circle id="circle_A">
  <circle id="circle_B">
</g>
```

If we separate the shape operations from painting, we can use `<mask>`.

```xml
<mask id="A_or_B">
  <circle id="circle_A" fill="#ffffff">
  <circle id="circle_B" fill="#ffffff">
</mask>
<rect mask="url(#A_or_B)">
```

Clip-path equivalent is the following:

```xml
<clipPath id="A_or_B">
  <circle id="circle_A">
  <circle id="circle_B">
</clipPath>
<rect clip-path="url(#A_or_B)">
```

The general conversion process would be:

1. Create a `<mask>` container
2. Append shapes to the current `<mask>` container
3. Apply the mask to the final target (`<rect>`)

## Subtraction (NOT OR)

Subtraction operation is equivalent to specifying `fill` to black (`#000000`).

```xml
<mask id="A_sub_B">
  <circle id="circle_A" fill="#ffffff" />
  <circle id="circle_B" fill="#000000" />
</mask>
<rect mask="url(#A_sub_B)">
```

It is not possible to directly use `<clipPath>` for subtraction.

## Intersection (AND)

Intersection is a chain of masks.

```xml
<mask id="A">
  <circle id="circle_A" fill="#ffffff">
</mask>
<mask id="A_and_B">
  <circle id="circle_B" fill="#ffffff" mask="url(#A)">
</mask>
<rect mask="url(#A_and_B)">
```

The general conversion process would be:

1. Create a `<mask>` container
2. For each shape, create a new `<mask>` container with the content referencing the previous `mask` container.

## XOR

XOR is a combination: (A OR B) AND NOT (A AND B).
Alternative formulation of XOR is available: (A AND NOT B) OR (NOT A AND B).
