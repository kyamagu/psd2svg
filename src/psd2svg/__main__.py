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
        "--images-path",
        metavar="PATH",
        type=str,
        default=None,
        help="Path to images directory relative to output.",
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
    convert(args.input, args.output, args.images_path)


if __name__ == "__main__":
    main()
