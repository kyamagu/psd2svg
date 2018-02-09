# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import argparse
import logging
import os
from psd2svg import psd2svg

def main():
    parser = argparse.ArgumentParser(description='Convert PSD file to SVG')
    parser.add_argument(
        'input', metavar='INPUT', type=str, help='Input PSD file path or URL')
    parser.add_argument(
        'output', metavar='PATH', type=str, nargs='?', default='.',
        help='Output file or directory. When directory is specified, filename'
             ' is automatically inferred from input')
    parser.add_argument(
        '--text-mode', metavar='MODE', default='image',
        help='Render texts in bitmap or vector. One of [image, image-only, '
             'text, text-only]. Default image')
    parser.add_argument(
        '--export-resource', action='store_true',
        help='Export image resources, default False')
    parser.add_argument(
        '--resource-prefix', metavar='PATH', type=str, default='.',
        help='Resource path prefix relative to output.')
    parser.add_argument(
        '--overwrite', action='store_true', help='Overwrite output')
    parser.add_argument(
        '--no-preview', action='store_true', help='Do not embed a preview')
    parser.add_argument(
        '--rasterizer', metavar='METHOD', default='chromium', type=str,
        help='Specify which rasterizer to use. default chromium.')
    parser.add_argument(
        '--loglevel', metavar='LEVEL', default='WARNING',
        help='Logging level, default WARNING')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.loglevel.upper(),
                                      'WARNING'))

    prefix, ext = os.path.splitext(args.output)
    if ext.lower() in (".png", ".jpg", ".jpeg", ".gif" ".tiff"):
        from psd2svg.rasterizer import create_rasterizer
        rasterizer = create_rasterizer(args.rasterizer)
        svg_file = prefix + ".svg"
        psd2svg(args.input, svg_file,
                resource_prefix=args.resource_prefix,
                text_mode=args.text_mode,
                export_resource=args.export_resource,
                overwrite=args.overwrite,
                no_preview=args.no_preview)
        image = rasterizer.rasterize(svg_file)
        image.save(args.output)
    else:
        psd2svg(args.input, args.output,
                resource_prefix=args.resource_prefix,
                text_mode=args.text_mode,
                export_resource=args.export_resource,
                overwrite=args.overwrite,
                no_preview=args.no_preview)


if __name__ == '__main__':
    main()
