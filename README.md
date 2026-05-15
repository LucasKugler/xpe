# xpe

*Finally, a commandline xpath tool that is easy to use.*

> **Note:** This is a fork of the original [charmparticle/xpe](https://github.com/charmparticle/xpe) project, maintained here at LucasKugler/xpe.

***What is this?***

xpe is a commandline xpath parser. Pipe in some textual data, supply it with an xpath expression, and it will dump the result to stdout. Perfect for shellscripting. For example:

    echo "<root><item>Test</item></root>" | xpe '//item/text()'
    # Output: Test

xpe parses XML by default. For HTML files, use the `--html` flag:

    echo "<html><body><h1>Hello</h1></body></html>" | xpe --html '//h1/text()'
    # Output: Hello

Alternatively, xpe can query a file for xpath expressions:

    xpe '//a/@href' somefile.htm

The order doesn't matter, so the following is also valid:

    xpe somefile.htm '//a/@href'


***How to install***

This is a Python project managed with [uv](https://github.com/astral-sh/uv):

    pip install uv
    uv pip install xpe

Or run directly with uv:

    uv run xpe '//xpath' input.xml
