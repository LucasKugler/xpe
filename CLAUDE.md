# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

xpe is a command-line XPath parser. It reads XML/HTML from stdin or a file and applies an XPath expression, printing results to stdout.

## Usage

```bash
# With uv (recommended for development)
uv run xpe '//title/text()'
echo "<html><title>Test</title></html>" | uv run xpe '//title/text()'

# With file
uv run xpe '//a/@href' somefile.html

# After installation
xpe '//title/text()'
```

## Running

```bash
uv run xpe '//xpath' [file]
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

Single-file script (`xpe.py`). Key flow:
1. Parse arguments with argparse (xpath expression, optional file)
2. Detect input source (stdin vs file)
3. Read input and detect encoding via chardet
4. Parse HTML with lxml's HTMLParser
5. Execute XPath and print results (handles both text and element results)