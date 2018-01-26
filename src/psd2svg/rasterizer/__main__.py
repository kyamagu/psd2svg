from psd2svg.rasterizer import create_rasterizer
from logging import getLogger

logger = getLogger(__name__)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Rasterize SVG file.")
    parser.add_argument("input", metavar="URL", type=str, help="Input URL.")
    parser.add_argument("--output", metavar="PATH", default="output.png",
                        help="Output file. default output.png")
    parser.add_argument("--loglevel", metavar="LEVEL", default="INFO",
                        help="Logging level, default INFO.")
    parser.add_argument("--size", metavar="WxH", type=str, default=None,
                        help="Size of the screen. default None")
    parser.add_argument('--type', metavar='TYPE', type=str,
                        default="inkscape", help='Rasterizer type.')

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel.upper()))
    size = tuple(args.size.split("x")) if args.size else None
    rasterizer = create_rasterizer(args.type)
    image = rasterizer.rasterize(args.input, size=size)
    image.save(args.output)


if __name__ == "__main__":
    main()
