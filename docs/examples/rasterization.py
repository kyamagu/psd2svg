"""Rasterization examples - converting SVG to raster images."""

from psd_tools import PSDImage
from psd2svg import SVGDocument
from psd2svg.rasterizer import create_rasterizer

# Example 1: Basic rasterization using SVGDocument
print("Example 1: Basic rasterization")
psdimage = PSDImage.open("input.psd")
document = SVGDocument.from_psd(psdimage)

# Rasterize using default settings (resvg)
image = document.rasterize()
image.save("output.png")
print("✓ Created output.png")

# Example 2: Rasterization with custom dimensions
print("\nExample 2: Custom dimensions")

# Fixed dimensions
image_800x600 = document.rasterize(width=800, height=600)
image_800x600.save("output_800x600.png")
print("✓ Created 800x600 image")

# Scale factor (2x original size)
image_2x = document.rasterize(scale=2.0)
image_2x.save("output_2x.png")
print("✓ Created 2x scaled image")

# Example 3: Using different rasterizer backends
print("\nExample 3: Different rasterizer backends")
svg_string = document.tostring(embed_images=True)

# resvg (recommended)
resvg = create_rasterizer("resvg")
img_resvg = resvg.rasterize_from_string(svg_string)
img_resvg.save("output_resvg.png")
print("✓ Rasterized with resvg")

# Chromium (requires Selenium + ChromeDriver)
try:
    chromium = create_rasterizer("chromium")
    img_chromium = chromium.rasterize_from_string(svg_string)
    img_chromium.save("output_chromium.png")
    print("✓ Rasterized with Chromium")
except Exception as e:
    print(f"⚠ Chromium rasterizer not available: {e}")

# Example 4: Rasterizing from file
print("\nExample 4: Rasterizing from SVG file")

# First save SVG
document.save("temp.svg", embed_images=True)

# Then rasterize from file
rasterizer = create_rasterizer("resvg")
image = rasterizer.rasterize("temp.svg")
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

    # Rasterize with thumbnail dimensions
    image = document.rasterize(width=size[0], height=size[1])

    # Apply thumbnail optimization
    image.thumbnail(size, resample=3)  # LANCZOS resampling
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

rasterizer = create_rasterizer("resvg")

for svg_file in svg_dir.glob("*.svg"):
    print(f"Rasterizing {svg_file.name}...")

    output_path = png_dir / f"{svg_file.stem}.png"
    image = rasterizer.rasterize(str(svg_file))
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
    psd_path: str, output_1x: str, output_2x: str, base_width: int
) -> None:
    """Render both 1x and 2x (Retina) versions.

    Args:
        psd_path: Path to PSD file
        output_1x: Path for 1x resolution output
        output_2x: Path for 2x resolution output
        base_width: Base width in pixels
    """
    psdimage = PSDImage.open(psd_path)
    document = SVGDocument.from_psd(psdimage)

    # Calculate aspect ratio
    aspect_ratio = psdimage.height / psdimage.width
    base_height = int(base_width * aspect_ratio)

    # Render 1x version
    img_1x = document.rasterize(width=base_width, height=base_height)
    img_1x.save(output_1x)

    # Render 2x version
    img_2x = document.rasterize(width=base_width * 2, height=base_height * 2)
    img_2x.save(output_2x)


render_for_retina("input.psd", "output@1x.png", "output@2x.png", 800)
print("✓ Created Retina-ready images")

# Example 9: Error handling for rasterization
print("\nExample 9: Rasterization with error handling")


def safe_rasterize(svg_path: str, output_path: str, backend: str = "resvg") -> bool:
    """Safely rasterize with error handling.

    Args:
        svg_path: Path to SVG file
        output_path: Path to save PNG
        backend: Rasterizer backend to use

    Returns:
        True if successful, False otherwise
    """
    try:
        rasterizer = create_rasterizer(backend)
        image = rasterizer.rasterize(svg_path)
        image.save(output_path)
        print(f"✓ Successfully rasterized {svg_path}")
        return True

    except FileNotFoundError:
        print(f"✗ File not found: {svg_path}")
        return False

    except Exception as e:
        print(f"✗ Rasterization failed: {e}")
        # Try fallback to resvg if another backend failed
        if backend != "resvg":
            print("  Trying resvg as fallback...")
            return safe_rasterize(svg_path, output_path, "resvg")
        return False


# Use it
success = safe_rasterize("input.svg", "output.png", "chromium")

print("\n✓ All rasterization examples completed")
