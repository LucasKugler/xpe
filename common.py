#!/usr/bin/env python3
"""Shared utilities for xpe, xte, and xve tools."""

from sys import stdin
from typing import Optional


def read_input(stdin_obj, file: Optional[str] = None) -> bytes:
    """
    Read input from file or stdin.

    Args:
        stdin_obj: The stdin object to read from
        file: Optional file path. If None, reads from stdin

    Returns:
        Raw bytes from file or stdin
    """
    if file:
        with open(file, "rb") as f:
            return f.read()
    else:
        return stdin_obj.buffer.read()


def read_content_or_file(
    parser, content: str, path: str, inline: bool, name: str
) -> bytes:
    """
    Read content from inline argument or file path.

    Args:
        parser: ArgumentParser for error reporting
        content: The content string (used if inline=True)
        path: The file path (used if inline=False)
        inline: Whether content is inline or from file
        name: Name of the content type for error messages

    Returns:
        Raw bytes of the content

    Raises:
        SystemExit: If file not found or cannot be read
    """
    if inline:
        return content.encode()
    else:
        try:
            with open(path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            parser.error(f"{name} file not found: {path}")
        except PermissionError:
            parser.error(f"Cannot read {name} file: {path}")
        return b""  # Never reached due to parser.error raising SystemExit
