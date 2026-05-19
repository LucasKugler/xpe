# xpe

*Finally, commandline XML tools that are easy to use.*

> **Note:** This is a fork of the original [charmparticle/xpe](https://github.com/charmparticle/xpe) project, maintained here at LucasKugler/xpe.

## xpe - XPath Parser

xpe is a commandline xpath parser. Pipe in some textual data, supply it with an xpath expression, and it will dump the result to stdout. Perfect for shellscripting. For example:

    echo "<root><item>Test</item></root>" | xpe '//item/text()'
    # Output: Test

xpe parses XML by default. For HTML files, use the `--html` flag:

    echo "<html><body><h1>Hello</h1></body></html>" | xpe --html '//h1/text()'
    # Output: Hello

Alternatively, xpe can query a file for xpath expressions:

    xpe '//a/@href' somefile.htm

## xte - XSLT Transformer

xte transforms XML using XSLT stylesheets:

    xte stylesheet.xsl input.xml
    cat input.xml | xte stylesheet.xsl

Inline stylesheet with `-s` flag:

    cat input.xml | xte -s '<?xml version="1.0"?><xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"><xsl:template match="/"><out><xsl:value-of select="//item"/></out></xsl:template></xsl:stylesheet>'

Stylesheet parameters with `-p` flag:

    echo "<root/>" | xte -s '...' -p "myvar=hello"
    echo "<root/>" | xte stylesheet.xsl -p "a=hello" -p "b=world"

## xve - XSD Validator

xve validates XML against XSD schemas:

    xve schema.xsd input.xml
    cat input.xml | xve schema.xsd

Inline schema with `-s` flag:

    echo '<root><item>Test</item></root>' | xve -s '<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="root"/></xs:schema>'

On success, no output. On failure, validation errors are printed to stderr.

## How to install

This is a Python project managed with [uv](https://github.com/astral-sh/uv):

    pip install uv
    uv pip install xpe

Or run directly with uv:

    uv run xpe '//xpath' input.xml
    uv run xte stylesheet.xsl input.xml
    uv run xve schema.xsd input.xml
