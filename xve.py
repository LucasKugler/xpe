#!/usr/bin/env python3

import argparse
from sys import stdin
from typing import Optional

from lxml import etree


def load_schema(schema_content: bytes) -> etree.XMLSchema:
    """
    Load and parse an XSD schema from bytes.

    Args:
        schema_content: Raw bytes of the XSD schema

    Returns:
        Compiled XMLSchema object

    Raises:
        ValueError: If the schema is invalid
    """
    try:
        schema_doc = etree.XML(schema_content)
        return etree.XMLSchema(schema_doc)
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XSD schema: {e}")


def validate_xml(xml_data: bytes, schema: etree.XMLSchema) -> bool:
    """
    Validate XML data against an XSD schema.

    Args:
        xml_data: Raw bytes of the XML document
        schema: Compiled XMLSchema object

    Returns:
        True if valid

    Raises:
        ValueError: If XML is invalid or doesn't match schema
    """
    try:
        doc = etree.fromstring(xml_data)
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML: {e}")

    if not schema.validate(doc):
        raise ValueError(f"XML validation failed:\n{schema.error_log}")

    return True


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
        schema = load_schema(schema_content)
    except ValueError as e:
        parser.error(str(e))

    if stdin.isatty() and args.file is None:
        parser.error("Either provide a file or pipe data to stdin")

    if args.file:
        with open(args.file, "rb") as f:
            raw = f.read()
    else:
        raw = stdin.buffer.read()

    try:
        validate_xml(raw, schema)
    except ValueError as e:
        parser.error(str(e))


if __name__ == "__main__":
    run()