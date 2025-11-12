"""Rasterization examples - converting SVG to raster images."""

from psd_tools import PSDImage
from psd2svg import SVGDocument
from psd2svg.rasterizer import ResvgRasterizer

# Example 1: Basic rasterization using SVGDocument
print("Example 1: Basic rasterization")
psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)

# Rasterize using default settings (resvg)
image = document.rasterize()
image.save("output.png")
print("✓ Created output.png")

# Example 2: Rasterization with custom DPI
print("\nExample 2: Custom DPI")

# Standard screen resolution
image_96dpi = document.rasterize(dpi=96)
image_96dpi.save("output_96dpi.png")
print("✓ Created 96 DPI image")

# High resolution for print
image_300dpi = document.rasterize(dpi=300)
image_300dpi.save("output_300dpi.png")
print("✓ Created 300 DPI image")

# Example 3: Using ResvgRasterizer directly
print("\nExample 3: Using ResvgRasterizer directly")
svg_string = document.tostring(embed_images=True)

# Create rasterizer instance
rasterizer = ResvgRasterizer(dpi=96)
img_resvg = rasterizer.from_string(svg_string)
img_resvg.save("output_resvg.png")
print("✓ Rasterized with resvg")

# Example 4: Rasterizing from file
print("\nExample 4: Rasterizing from SVG file")

# First save SVG
document.save("temp.svg", embed_images=True)

# Then rasterize from file
rasterizer = ResvgRasterizer()
image = rasterizer.from_file("temp.svg")
image.save("from_file.png")
print("✓ Rasterized from SVG file")

# Example 5: Creating thumbnails
print("\nExample 5: Creating thumbnails")


def create_thumbnail(psd_path: str, output_path: str, size: tuple[int, int]) -> None:
    """Create a thumbnail from PSD file.

    Args:
        psd_path: Path to PSD file
        output_path: Path to save thumbnail
        size: Thumbnail size (width, height)
    """
    psdimage = PSDImage.open(psd_path)
    document = SVGDocument.from_psd(psdimage)

    # Rasterize first
    image = document.rasterize()

    # Apply thumbnail optimization
    from PIL import Image

    image.thumbnail(size, resample=Image.Resampling.LANCZOS)
    image.save(output_path, optimize=True)


# Create various thumbnail sizes
create_thumbnail("input.psd", "thumb_small.png", (150, 150))
create_thumbnail("input.psd", "thumb_medium.png", (300, 300))
create_thumbnail("input.psd", "thumb_large.png", (600, 600))
print("✓ Created thumbnails")

# Example 6: Batch rasterization
print("\nExample 6: Batch rasterization")
from pathlib import Path

svg_dir = Path("svg_files")
png_dir = Path("png_output")
png_dir.mkdir(exist_ok=True)

rasterizer = ResvgRasterizer()

for svg_file in svg_dir.glob("*.svg"):
    print(f"Rasterizing {svg_file.name}...")

    output_path = png_dir / f"{svg_file.stem}.png"
    image = rasterizer.from_file(str(svg_file))
    image.save(output_path)

    print(f"✓ Created {output_path}")

# Example 7: Different output formats
print("\nExample 7: Different output formats")
psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)
image = document.rasterize()

# PNG - lossless
image.save("output.png", format="PNG", optimize=True)

# JPEG - lossy
image.convert("RGB").save("output.jpg", format="JPEG", quality=95)

# WebP - modern format
image.save("output.webp", format="WEBP", quality=90)

print("✓ Created images in multiple formats")

# Example 8: High-DPI rendering
print("\nExample 8: High-DPI rendering")


def render_for_retina(
    psd_path: str, output_1x: str, output_2x: str, base_dpi: int = 96
) -> None:
    """Render both 1x and 2x (Retina) versions.

    Args:
        psd_path: Path to PSD file
        output_1x: Path for 1x resolution output
        output_2x: Path for 2x resolution output
        base_dpi: Base DPI (default 96)
    """
    psdimage = PSDImage.open(psd_path)
    document = SVGDocument.from_psd(psdimage)

    # Render 1x version
    img_1x = document.rasterize(dpi=base_dpi)
    img_1x.save(output_1x)

    # Render 2x version
    img_2x = document.rasterize(dpi=base_dpi * 2)
    img_2x.save(output_2x)


render_for_retina("input.psd", "output@1x.png", "output@2x.png")
print("✓ Created Retina-ready images")

# Example 9: Error handling for rasterization
print("\nExample 9: Rasterization with error handling")


def safe_rasterize(svg_path: str, output_path: str, dpi: int = 96) -> bool:
    """Safely rasterize with error handling.

    Args:
        svg_path: Path to SVG file
        output_path: Path to save PNG
        dpi: DPI setting for rasterization

    Returns:
        True if successful, False otherwise
    """
    try:
        rasterizer = ResvgRasterizer(dpi=dpi)
        image = rasterizer.from_file(svg_path)
        image.save(output_path)
        print(f"✓ Successfully rasterized {svg_path}")
        return True

    except FileNotFoundError:
        print(f"✗ File not found: {svg_path}")
        return False

    except Exception as e:
        print(f"✗ Rasterization failed: {e}")
        return False


# Use it
success = safe_rasterize("input.svg", "output.png", dpi=96)

# Example 10: Custom image processing after rasterization
print("\nExample 10: Custom image processing")
from PIL import Image, ImageFilter

psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)
image = document.rasterize()

# Add white background
background = Image.new("RGB", image.size, (255, 255, 255))
background.paste(image, (0, 0), image)
background.save("output_white_bg.png")
print("✓ Created image with white background")

# Apply blur effect
blurred = image.filter(ImageFilter.GaussianBlur(radius=5))
blurred.save("output_blurred.png")
print("✓ Created blurred image")

# Resize image
from PIL import Image

resized = image.resize((800, 600), Image.Resampling.LANCZOS)
resized.save("output_resized.png")
print("✓ Created resized image")

print("\n✓ All rasterization examples completed")
