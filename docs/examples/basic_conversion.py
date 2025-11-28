"""Basic PSD to SVG conversion examples."""

from psd_tools import PSDImage
from psd2svg import SVGDocument, convert

# Example 1: Simple conversion using convert() function
# This is the easiest way to convert a PSD file
print("Example 1: Simple conversion")
convert("input.psd", "output.svg")
print("✓ Created output.svg with embedded images")

# Example 2: Conversion with external images
print("\nExample 2: External images")
convert("input.psd", "output.svg", image_prefix="images/img")
print("✓ Created output.svg and images/img*.webp files")

# Example 3: Using SVGDocument for more control
print("\nExample 3: Using SVGDocument")
psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)

# Save with embedded images
document.save("embedded.svg", embed_images=True)
print("✓ Created embedded.svg")

# Save with external PNG images
document.save("external.svg", image_prefix="img", image_format="png")
print("✓ Created external.svg and img*.png files")

# Example 4: Get SVG as string
print("\nExample 4: Get SVG as string")
svg_string = document.tostring(embed_images=True)
print(f"✓ Generated SVG string ({len(svg_string)} characters)")

# Example 5: Export and load
print("\nExample 5: Export and load")
exported = document.export()
print(f"✓ Exported document with {len(exported['images'])} images")

# Load it back
reloaded = SVGDocument.load(exported["svg"], exported["images"])
print("✓ Reloaded document successfully")
