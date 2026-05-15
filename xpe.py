#!/usr/bin/env python3

import argparse
from sys import stdin

from lxml import etree
from chardet import detect


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
    if not xpath or xpath[0] not in "/(":
        parser.error("XPath expression must start with '/' or '('")

    target = args.file

    if stdin.isatty() and target is None:
        parser.error("Either provide a file or pipe data to stdin")

    if target:
        bytelines = open(target, "rb")
    else:
        bytelines = stdin.buffer

    html = ""
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
            html += line

        i += 1

    bytelines.close()

    parser_obj = etree.HTMLParser() if args.html else None
    tree = etree.fromstring(html, parser_obj)

    try:
        xpaths = tree.xpath(xpath)
    except etree.XPathEvalError:
        parser.error("Invalid XPath expression")

    for xpath in xpaths:
        if type(xpath) == etree._ElementUnicodeResult:
            print(xpath)
        else:
            print(xpath.text)


if __name__ == "__main__":
    run()