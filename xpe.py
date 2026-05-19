#!/usr/bin/env python3

import argparse
from sys import stdin

from lxml import etree


def run():
    parser = argparse.ArgumentParser(
        description="A commandline xpath tool that is easy to use",
        prog="xpe",
    )
    parser.add_argument(
        "xpath",
        help="XPath expression to evaluate",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="File to parse (reads from stdin if not provided or when piping)",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Parse as HTML instead of XML",
    )
    args = parser.parse_args()

    xpath = args.xpath.strip("\"'")
    if not xpath:
        parser.error("XPath expression cannot be empty")

    if stdin.isatty() and args.file is None:
        parser.error("Either provide a file or pipe data to stdin")

    if args.file:
        with open(args.file, "rb") as f:
            raw = f.read()
    else:
        raw = stdin.buffer.read()

    parser_obj = etree.HTMLParser() if args.html else None
    tree = etree.fromstring(raw, parser_obj)

    try:
        xpaths = tree.xpath(xpath)
    except etree.XPathEvalError:
        parser.error("Invalid XPath expression")

    for xpath in xpaths:
        if type(xpath) == etree._ElementUnicodeResult:
            print(xpath.rstrip())
        else:
            print(etree.tostring(xpath, encoding="unicode", ).rstrip())


if __name__ == "__main__":
    run()