import argparse
import logging

from psd2svg import convert


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Convert PSD file to SVG")
    parser.add_argument(
        "input", metavar="INPUT", type=str, help="Input PSD file path or URL"
    )
    parser.add_argument(
        "output",
        metavar="PATH",
        type=str,
        nargs="?",
        default=".",
        help="Output file.",
    )
    parser.add_argument(
        "--image-prefix",
        metavar="PATH",
        type=str,
        default=None,
        help="Path prefix for saving extracted images relative to output.",
    )
    parser.add_argument(
        "--no-text",
        dest="enable_text",
        action="store_false",
        help="Disable text layer conversion (rasterize text instead).",
    )
    parser.add_argument(
        "--no-live-shapes",
        dest="enable_live_shapes",
        action="store_false",
        help="Disable live shape conversion (use paths instead of shape primitives).",
    )
    parser.add_argument(
        "--no-title",
        dest="enable_title",
        action="store_false",
        help="Disable insertion of <title> elements with layer names.",
    )
    parser.add_argument(
        "--image-format",
        metavar="FORMAT",
        type=str,
        choices=["webp", "png", "jpeg"],
        default="webp",
        help="Image format for rasterized layers (webp, png, jpeg). Default: webp",
    )
    parser.add_argument(
        "--text-letter-spacing-offset",
        metavar="OFFSET",
        type=float,
        default=0.0,
        help="Global offset (in pixels) to add to letter-spacing values. Default: 0.0",
    )
    parser.add_argument(
        "--loglevel",
        metavar="LEVEL",
        default="WARNING",
        help="Logging level, default WARNING",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to convert PSD to SVG or raster image."""
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel.upper(), "WARNING"))
    convert(
        args.input,
        args.output,
        image_prefix=args.image_prefix,
        enable_text=args.enable_text,
        enable_live_shapes=args.enable_live_shapes,
        enable_title=args.enable_title,
        image_format=args.image_format,
        text_letter_spacing_offset=args.text_letter_spacing_offset,
    )


if __name__ == "__main__":
    main()
