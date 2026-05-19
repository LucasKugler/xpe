#!/usr/bin/env python3

import argparse
from sys import stdin

from lxml import etree


def run():
    parser = argparse.ArgumentParser(
        description="A commandline XSD validation tool",
        prog="xve",
    )
    parser.add_argument(
        "schema",
        help="Path to XSD schema file (or inline XSD if -s is used)",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="XML file to validate (reads from stdin if not provided or when piping)",
    )
    parser.add_argument(
        "-s",
        "--schema",
        dest="inline_schema",
        action="store_true",
        help="Treat schema argument as inline XSD content instead of a file path",
    )
    args = parser.parse_args()

    if args.inline_schema:
        schema_content = args.schema.encode()
    else:
        try:
            with open(args.schema, "rb") as f:
                schema_content = f.read()
        except FileNotFoundError:
            parser.error(f"Schema file not found: {args.schema}")
        except PermissionError:
            parser.error(f"Cannot read schema file: {args.schema}")

    try:
        schema_doc = etree.XML(schema_content)
        schema = etree.XMLSchema(schema_doc)
    except etree.XMLSyntaxError as e:
        parser.error(f"Invalid XSD schema: {e}")

    if stdin.isatty() and args.file is None:
        parser.error("Either provide a file or pipe data to stdin")

    if args.file:
        with open(args.file, "rb") as f:
            raw = f.read()
    else:
        raw = stdin.buffer.read()

    try:
        doc = etree.fromstring(raw)
    except etree.XMLSyntaxError as e:
        parser.error(f"Invalid XML: {e}")

    if schema.validate(doc):
        pass
    else:
        parser.error(f"XML validation failed:\n{schema.error_log}")


if __name__ == "__main__":
    run()