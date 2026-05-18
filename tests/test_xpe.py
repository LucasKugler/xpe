import subprocess
import sys
from pathlib import Path

import pytest

XPE = [sys.executable, "-m", "xpe"]


def run_xpe(xpath, input_data=None):
    result = subprocess.run(
        XPE + [xpath],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return result


class TestXPathSelection:
    def test_text_selection(self):
        result = run_xpe("//title/text()", "<html><title>Hello</title></html>")
        assert result.returncode == 0
        assert result.stdout.strip() == "Hello"

    def test_attribute_selection(self):
        result = run_xpe('//a/@href', '<a href="https://example.com">Link</a>')
        assert result.returncode == 0
        assert result.stdout.strip() == "https://example.com"

    def test_element_selection(self):
        result = run_xpe("//title", "<html><title>Hello</title></html>")
        assert result.returncode == 0
        assert "Hello" in result.stdout

    def test_multiple_results(self):
        result = run_xpe(
            "//li/text()", "<ul><li>One</li><li>Two</li><li>Three</li></ul>"
        )
        assert result.returncode == 0
        assert "One" in result.stdout
        assert "Two" in result.stdout
        assert "Three" in result.stdout


class TestInputSources:
    def test_stdin_input(self):
        result = run_xpe("//title/text()", "<html><title>From Stdin</title></html>")
        assert result.returncode == 0
        assert result.stdout.strip() == "From Stdin"

    def test_file_input(self, tmp_path):
        test_file = tmp_path / "test.html"
        test_file.write_text("<html><title>From File</title></html>")
        result = subprocess.run(
            XPE + ["//title/text()", str(test_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "From File"


class TestArgumentValidation:
    def test_missing_xpath(self):
        result = run_xpe("", "<html></html>")
        assert result.returncode == 2

    def test_invalid_xpath(self):
        result = run_xpe("//[invalid", "<html></html>")
        assert result.returncode == 2

    def test_relative_xpath(self):
        result = run_xpe("title", "<html><title>Test</title></html>")
        assert result.returncode == 0
        assert "<title>Test</title>" in result.stdout

    def test_no_input(self):
        result = subprocess.run(XPE + ["//title"], capture_output=True)
        assert result.returncode == 2


class TestEdgeCases:
    def test_empty_result(self):
        result = run_xpe("//nonexistent/text()", "<html><title>Test</title></html>")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_nested_elements(self):
        result = run_xpe(
            "//div/p/span/text()", "<div><p><span>Nested</span></p></div>"
        )
        assert result.returncode == 0
        assert "Nested" in result.stdout