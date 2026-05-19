import subprocess
import sys
from pathlib import Path

import pytest
from lxml import etree

from xpe import evaluate_xpath, format_result

XPE = [sys.executable, "-m", "xpe"]


def run_xpe(xpath, input_data=None):
    result = subprocess.run(
        XPE + [xpath],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return result


def run_xpe_direct(xpath, input_data: bytes):
    """Direct function call for coverage."""
    results = evaluate_xpath(xpath, input_data)
    return [format_result(r) for r in results]


class TestXPathSelection:
    def test_text_selection(self):
        result = run_xpe("//title/text()", "<html><title>Hello</title></html>")
        assert result.returncode == 0
        assert result.stdout.strip() == "Hello"

    def test_text_selection_direct(self):
        """Direct function call for coverage."""
        results = run_xpe_direct("//title/text()", b"<html><title>Hello</title></html>")
        assert len(results) == 1
        assert results[0] == "Hello"

    def test_attribute_selection(self):
        result = run_xpe('//a/@href', '<a href="https://example.com">Link</a>')
        assert result.returncode == 0
        assert result.stdout.strip() == "https://example.com"

    def test_attribute_selection_direct(self):
        """Direct function call for coverage."""
        results = run_xpe_direct('//a/@href', b'<a href="https://example.com">Link</a>')
        assert len(results) == 1
        assert results[0] == "https://example.com"

    def test_element_selection(self):
        result = run_xpe("//title", "<html><title>Hello</title></html>")
        assert result.returncode == 0
        assert "Hello" in result.stdout

    def test_element_selection_direct(self):
        """Direct function call for coverage."""
        results = run_xpe_direct("//title", b"<html><title>Hello</title></html>")
        assert len(results) == 1
        assert "Hello" in results[0]

    def test_multiple_results(self):
        result = run_xpe(
            "//li/text()", "<ul><li>One</li><li>Two</li><li>Three</li></ul>"
        )
        assert result.returncode == 0
        assert "One" in result.stdout
        assert "Two" in result.stdout
        assert "Three" in result.stdout

    def test_multiple_results_direct(self):
        """Direct function call for coverage."""
        results = run_xpe_direct("//li/text()", b"<ul><li>One</li><li>Two</li><li>Three</li></ul>")
        assert len(results) == 3
        assert results == ["One", "Two", "Three"]


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

    def test_empty_result_direct(self):
        """Direct function call for coverage."""
        results = run_xpe_direct("//nonexistent/text()", b"<html><title>Test</title></html>")
        assert len(results) == 0

    def test_nested_elements(self):
        result = run_xpe(
            "//div/p/span/text()", "<div><p><span>Nested</span></p></div>"
        )
        assert result.returncode == 0
        assert "Nested" in result.stdout

    def test_nested_elements_direct(self):
        """Direct function call for coverage."""
        results = run_xpe_direct("//div/p/span/text()", b"<div><p><span>Nested</span></p></div>")
        assert len(results) == 1
        assert results[0] == "Nested"

    def test_invalid_xpath_raises(self):
        """Test that invalid XPath raises ValueError."""
        with pytest.raises(ValueError, match="Invalid XPath"):
            evaluate_xpath("//[invalid", b"<html></html>")