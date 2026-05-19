#!/usr/bin/env python3

import argparse
from sys import stdin
from typing import Optional

from lxml import etree


def transform_xml(xml_data: bytes, stylesheet_content: bytes, xsl_params: Optional[dict] = None) -> str:
    """
    Transform XML data using an XSLT stylesheet.

    Args:
        xml_data: Raw bytes of the XML document
        stylesheet_content: Raw bytes of the XSLT stylesheet
        xsl_params: Dictionary of XSLT parameters

    Returns:
        Transformed XML as string
    """
    try:
        transform = etree.XSLT(etree.XML(stylesheet_content))
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XSLT stylesheet: {e}")

    try:
        doc = etree.fromstring(xml_data)
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML: {e}")

    if xsl_params:
        try:
            result = transform(doc, **xsl_params)
        except etree.XSLTApplyError as e:
            raise ValueError(f"XSLT transformation failed: {e}")
    else:
        result = transform(doc)

    return str(result)


def parse_xslt_params(param_list: list) -> dict:
    """
    Parse XSLT parameters from command-line format.

    Args:
        param_list: List of "NAME=VALUE" strings

    Returns:
        Dictionary of XSLT parameters
    """
    xsl_params = {}
    if param_list:
        for p in param_list:
            if "=" in p:
                name, value = p.split("=", 1)
                xsl_params[name] = etree.XSLT.strparam(value)
    return xsl_params


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

    if stdin.isatty() and args.file is None:
        parser.error("Either provide a file or pipe data to stdin")

    # Read input
    if args.file:
        with open(args.file, "rb") as f:
            raw = f.read()
    else:
        raw = stdin.buffer.read()

    xsl_params = parse_xslt_params(args.param)

    try:
        result = transform_xml(raw, stylesheet_content, xsl_params)
    except ValueError as e:
        parser.error(str(e))

    print(result)


if __name__ == "__main__":
    run()