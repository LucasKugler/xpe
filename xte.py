#!/usr/bin/env python3

import argparse
from sys import stdin, exit

from lxml import etree
from chardet import detect


def run():
    parser = argparse.ArgumentParser(
        description="A commandline xslt transformation tool",
        prog="xte",
    )
    parser.add_argument(
        "stylesheet",
        help="Path to XSLT stylesheet file (or inline XSLT if -s is used)",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="XML file to transform (reads from stdin if not provided or when piping)",
    )
    parser.add_argument(
        "-s",
        "--stylesheet",
        dest="inline_stylesheet",
        action="store_true",
        help="Treat stylesheet argument as inline XSLT content instead of a file path",
    )
    parser.add_argument(
        "-p",
        "--param",
        action="append",
        metavar="NAME=VALUE",
        help="XSLT parameter (can be used multiple times)",
    )
    args = parser.parse_args()

    # Read and validate stylesheet first
    if args.inline_stylesheet:
        stylesheet_content = args.stylesheet.encode()
    else:
        try:
            with open(args.stylesheet, "rb") as f:
                stylesheet_content = f.read()
        except FileNotFoundError:
            parser.error(f"Stylesheet file not found: {args.stylesheet}")
        except PermissionError:
            parser.error(f"Cannot read stylesheet file: {args.stylesheet}")

    try:
        transform = etree.XSLT(etree.XML(stylesheet_content))
    except etree.XMLSyntaxError as e:
        parser.error(f"Invalid XSLT stylesheet: {e}")

    if stdin.isatty() and args.file is None:
        parser.error("Either provide a file or pipe data to stdin")

    # Read input
    if args.file:
        bytelines = open(args.file, "rb")
    else:
        bytelines = stdin.buffer

    xml_content = ""
    i = 0
    for bline in bytelines:
        if i == 0:
            try:
                if "encoding=" in bline.decode():
                    continue
            except Exception:
                pass

        guess = detect(bline)
        if guess["encoding"] is not None:
            line = bline.decode(guess["encoding"], errors="ignore")
            xml_content += line

        i += 1

    bytelines.close()

    # Parse and transform
    try:
        doc = etree.fromstring(xml_content.encode())
    except etree.XMLSyntaxError as e:
        parser.error(f"Invalid XML: {e}")

    xsl_params = {}
    if args.param:
        for p in args.param:
            if "=" in p:
                name, value = p.split("=", 1)
                xsl_params[name] = etree.XSLT.strparam(value)

    try:
        result = transform(doc, **xsl_params)
    except etree.XSLTApplyError as e:
        parser.error(f"XSLT transformation failed: {e}")

    # Output result
    print(str(result))


if __name__ == "__main__":
    run()