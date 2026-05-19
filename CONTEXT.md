# CONTEXT.md

This file provides guidance to agents working with code in this repository.

## Project Overview

Three command-line XML/HTML tools:

- **xpe** - XPath parser: extracts data using XPath expressions
- **xte** - XSLT transformer: transforms XML using XSLT stylesheets
- **xve** - XSD validator: validates XML against XSD schemas

All tools read from stdin or files and output results to stdout.

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
cat input.xml | uv run xte -s 'XSLT_CONTENT'
# With XSLT parameters
uv run xte stylesheet.xsl input.xml -p "param1=value1" -p "param2=value2"

# xve - XSD validation
uv run xve schema.xsd input.xml
cat input.xml | uv run xve schema.xsd
# Inline schema with -s flag
cat input.xml | uv run xve -s 'XSD_CONTENT'
```

## Dependencies

Managed via `pyproject.toml` with hatch/uv. Dependencies:
- `lxml>=4.9.0` - XML/HTML parsing

Dev dependencies:
- `pytest>=8.3.5`
- `pytest-cov>=5.0.0`

## Testing

```bash
uv run pytest           # run all tests
uv run pytest test_xpe.py::TestXPathSelection::test_text_selection  # run single test
```

## Architecture

All three tools (`xpe.py`, `xte.py`, `xve.py`) share similar structure:
1. Parse arguments with argparse (path, optional input file)
2. Read input using `common.read_input()`
3. Parse XML/HTML with lxml
4. Process (transform/query/validate) and print results

Common utilities in `common.py`:
- `read_input()` - Read from file or stdin
- `read_content_or_file()` - Read inline content or file

Entry points defined in `pyproject.toml`:
- `xpe = "xpe:run"`
- `xte = "xte:run"`
- `xve = "xve:run"`