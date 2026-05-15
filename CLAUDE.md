# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Two command-line XML/HTML tools:

- **xpe** - XPath parser: extracts data using XPath expressions
- **xte** - XSLT transformer: transforms XML using XSLT stylesheets

Both read from stdin or files and output results to stdout.

## Usage

```bash
# xpe - XPath expressions (XML by default)
uv run xpe '//title/text()'
echo "<root><item>Test</item></root>" | uv run xpe '//item/text()'
# Use --html for HTML files
echo "<html><title>Test</title></html>" | uv run xpe --html '//title/text()'
uv run xpe '//a/@href' somefile.html

# xte - XSLT transformations
uv run xte stylesheet.xsl input.xml
cat input.xml | uv run xte stylesheet.xsl
# Inline stylesheet with -s flag
cat input.xml | uv run xte -s '<?xml version="1.0"?><xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"><xsl:template match="/"><out><xsl:value-of select="//item"/></out></xsl:template></xsl:stylesheet>'
```

Requires: `lxml`, `chardet`

## Dependencies

Managed via `pyproject.toml` with uv. Dependencies:
- `lxml` - XML/HTML parsing
- `chardet` - encoding detection

## Testing

```bash
uv run pytest           # run all tests
uv run pytest test_xpe.py::TestXPathSelection::test_text_selection  # run single test
```

## Architecture

`xpe.py` and `xte.py` share similar structure:
1. Parse arguments with argparse (stylesheet/path, optional input file)
2. Detect input source (stdin vs file)
3. Read input and detect encoding via chardet
4. Parse XML/HTML with lxml
5. Transform (xte) or query (xpe) and print results