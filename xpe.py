#!/usr/bin/env python3

import argparse
from sys import stdin

from lxml import etree

from common import read_input


def evaluate_xpath(xpath_expr: str, xml_data: bytes, html: bool = False) -> list:
    """
    Evaluate an XPath expression on XML/HTML data.

    Args:
        xpath_expr: The XPath expression to evaluate
        xml_data: Raw bytes of the XML/HTML document
        html: Whether to parse as HTML instead of XML

    Returns:
        List of XPath results
    """
    parser_obj = etree.HTMLParser() if html else None
    tree = etree.fromstring(xml_data, parser_obj)

    try:
        results = tree.xpath(xpath_expr)
    except etree.XPathEvalError:
        raise ValueError(f"Invalid XPath expression: {xpath_expr}")

    return results


def format_result(result) -> str:
    """
    Format an XPath result for output.

    Args:
        result: An XPath result (text, attribute, or element)

    Returns:
        Formatted string representation
    """
    if type(result) == etree._ElementUnicodeResult:
        return result.rstrip()
    else:
        return etree.tostring(result, encoding="unicode").rstrip()


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

    raw = read_input(stdin, args.file)

    try:
        xpaths = evaluate_xpath(xpath, raw, args.html)
    except ValueError as e:
        parser.error(str(e))

    for xpath in xpaths:
        print(format_result(xpath))


if __name__ == "__main__":
    run()