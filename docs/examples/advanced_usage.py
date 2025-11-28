"""Advanced usage examples for psd2svg."""

from pathlib import Path
from psd_tools import PSDImage
from psd2svg import SVGDocument

# Example 1: Batch conversion
print("Example 1: Batch conversion")
input_dir = Path("input_psds")
output_dir = Path("output_svgs")
output_dir.mkdir(exist_ok=True)

for psd_file in input_dir.glob("*.psd"):
    print(f"Converting {psd_file.name}...")
    psdimage = PSDImage.open(psd_file)
    document = SVGDocument.from_psd(psdimage)

    # Save with external images
    svg_path = output_dir / f"{psd_file.stem}.svg"
    image_dir = output_dir / "images"
    image_dir.mkdir(exist_ok=True)

    document.save(
        str(svg_path),
        image_prefix=f"images/{psd_file.stem}",
        image_format="webp",
    )
    print(f"✓ Created {svg_path}")

# Example 2: Different image formats
print("\nExample 2: Image format comparison")
psdimage = PSDImage.open("photo.psd")
document = SVGDocument.from_psd(psdimage)

# PNG - lossless, larger file
document.save("output_png.svg", image_prefix="img", image_format="png")

# WebP - modern, good compression
document.save("output_webp.svg", image_prefix="img", image_format="webp")

# JPEG - lossy, smallest file
document.save("output_jpeg.svg", image_prefix="img", image_format="jpeg")

print("✓ Created files with different image formats")

# Example 3: Working with layers
print("\nExample 3: Inspecting PSD layers")
psdimage = PSDImage.open("complex.psd")

print(f"Document size: {psdimage.width}x{psdimage.height}")
print(f"Number of layers: {len(list(psdimage.descendants()))}")

# List all visible layers
print("\nVisible layers:")
for layer in psdimage.descendants():
    if layer.visible:
        print(f"  - {layer.name} ({layer.kind})")

# Convert to SVG
document = SVGDocument.from_psd(psdimage)
document.save("complex.svg", embed_images=True)
print("✓ Converted complex document")

# Example 4: Memory-efficient processing
print("\nExample 4: Memory-efficient processing")
# For very large PSDs, convert and save immediately
psdimage = PSDImage.open("large.psd")
document = SVGDocument.from_psd(psdimage)
document.save("large.svg", image_prefix="large", image_format="webp")
del document
del psdimage
print("✓ Processed large file and freed memory")

# Example 5: Error handling
print("\nExample 5: Error handling")


def convert_with_error_handling(input_path: str, output_path: str) -> bool:
    """Convert PSD with proper error handling."""
    try:
        psdimage = PSDImage.open(input_path)
        document = SVGDocument.from_psd(psdimage)
        document.save(output_path, embed_images=True)
        print(f"✓ Successfully converted {input_path}")
        return True

    except FileNotFoundError:
        print(f"✗ File not found: {input_path}")
        return False

    except PermissionError:
        print(f"✗ Permission denied: {output_path}")
        return False

    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False


# Use it
success = convert_with_error_handling("input.psd", "output.svg")

# Example 6: Custom output organization
print("\nExample 6: Organized output structure")
base_name = "project"
output_root = Path("output")

# Create organized directory structure
svg_dir = output_root / "svg"
images_dir = output_root / "images" / base_name
svg_dir.mkdir(parents=True, exist_ok=True)
images_dir.mkdir(parents=True, exist_ok=True)

psdimage = PSDImage.open("project.psd")
document = SVGDocument.from_psd(psdimage)

# Save with relative paths
document.save(
    str(svg_dir / f"{base_name}.svg"),
    image_prefix=f"../images/{base_name}/{base_name}",
    image_format="webp",
)
print(f"✓ Created organized output structure in {output_root}")
