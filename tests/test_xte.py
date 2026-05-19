import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest
from lxml import etree

from xte import transform_xml, parse_xslt_params

XTE = [sys.executable, "-m", "xte"]


def run_xte(stylesheet_path, input_data=None):
    result = subprocess.run(
        XTE + [stylesheet_path],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return result


def run_xte_direct(xml_data: bytes, xsl_data: bytes, params: Optional[dict] = None):
    """Direct function call for coverage."""
    return transform_xml(xml_data, xsl_data, params)


@pytest.fixture
def simple_xsl(tmp_path):
    xsl = tmp_path / "identity.xsl"
    xsl.write_text(
        """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>"""
    )
    return xsl


@pytest.fixture
def extract_xsl(tmp_path):
    xsl = tmp_path / "extract.xsl"
    xsl.write_text(
        """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <items>
      <xsl:for-each select="//item">
        <item><xsl:value-of select="."/></item>
      </xsl:for-each>
    </items>
  </xsl:template>
</xsl:stylesheet>"""
    )
    return xsl


class TestBasicTransformation:
    def test_identity_transform(self, simple_xsl):
        xml = '<?xml version="1.0"?><root><item>Hello</item></root>'
        result = run_xte(str(simple_xsl), xml)
        assert result.returncode == 0
        assert "<root>" in result.stdout
        assert "<item>Hello</item>" in result.stdout

    def test_identity_transform_direct(self, simple_xsl):
        """Direct function call for coverage."""
        xml = '<?xml version="1.0"?><root><item>Hello</item></root>'
        result = run_xte_direct(xml.encode(), simple_xsl.read_bytes())
        assert "<root>" in result
        assert "<item>Hello</item>" in result

    def test_extract_items(self, extract_xsl):
        xml = """<?xml version="1.0"?>
<root>
  <item>One</item>
  <item>Two</item>
  <item>Three</item>
</root>"""
        result = run_xte(str(extract_xsl), xml)
        assert result.returncode == 0
        assert "<items>" in result.stdout
        assert "One" in result.stdout
        assert "Two" in result.stdout
        assert "Three" in result.stdout

    def test_extract_items_direct(self, extract_xsl):
        """Direct function call for coverage."""
        xml = """<?xml version="1.0"?>
<root>
  <item>One</item>
  <item>Two</item>
  <item>Three</item>
</root>"""
        result = run_xte_direct(xml.encode(), extract_xsl.read_bytes())
        assert "<items>" in result
        assert "One" in result
        assert "Two" in result
        assert "Three" in result


class TestInputSources:
    def test_stdin_input(self, simple_xsl):
        xml = '<?xml version="1.0"?><root><item>From Stdin</item></root>'
        result = run_xte(str(simple_xsl), xml)
        assert result.returncode == 0
        assert "From Stdin" in result.stdout

    def test_file_input(self, tmp_path, simple_xsl):
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><root><item>From File</item></root>')
        result = subprocess.run(
            XTE + [str(simple_xsl), str(xml_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "From File" in result.stdout


class TestArgumentValidation:
    def test_missing_stylesheet(self):
        result = subprocess.run(XTE + [], capture_output=True)
        assert result.returncode == 2

    def test_missing_input(self):
        xsl = "<?xml version='1.0'?><xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'><xsl:template match='/'><xsl:text>test</xsl:text></xsl:template></xsl:stylesheet>"
        result = subprocess.run(XTE + ["-s", xsl], capture_output=True)
        assert result.returncode == 2

    def test_stylesheet_not_found(self):
        result = subprocess.run(XTE + ["nonexistent.xsl"], capture_output=True)
        assert result.returncode == 2
        stderr = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
        assert "not found" in stderr.lower()

    def test_invalid_stylesheet(self, tmp_path):
        invalid_xsl = tmp_path / "invalid.xsl"
        invalid_xsl.write_text("not valid xslt")
        result = subprocess.run(
            XTE + [str(invalid_xsl)],
            input="<root/>",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XSLT" in result.stderr

    def test_invalid_stylesheet_inline(self):
        result = subprocess.run(
            XTE + ["-s", "not valid xslt"],
            input="<root/>",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XSLT" in result.stderr

    def test_invalid_xml(self, simple_xsl):
        result = subprocess.run(
            XTE + [str(simple_xsl)],
            input="not valid xml",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XML" in result.stderr


class TestInlineStylesheet:
    def test_inline_stylesheet(self):
        xsl = "<?xml version='1.0'?><xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'><xsl:template match='/'><result><xsl:value-of select='//item'/></result></xsl:template></xsl:stylesheet>"
        xml = '<?xml version="1.0"?><root><item>Inline Test</item></root>'
        result = subprocess.run(
            XTE + ["-s", xsl],
            input=xml,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Inline Test" in result.stdout


class TestXSLTFeatures:
    def test_attribute_extraction(self, tmp_path):
        xsl = tmp_path / "attr.xsl"
        xsl.write_text(
            """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <hrefs>
      <xsl:for-each select="//a/@href">
        <href><xsl:value-of select="."/></href>
      </xsl:for-each>
    </hrefs>
  </xsl:template>
</xsl:stylesheet>"""
        )
        xml = '<?xml version="1.0"?><root><a href="https://example.com"/><a href="https://test.com"/></root>'
        result = run_xte(str(xsl), xml)
        assert result.returncode == 0
        assert "https://example.com" in result.stdout
        assert "https://test.com" in result.stdout

    def test_attribute_extraction_direct(self, tmp_path):
        """Direct function call for coverage."""
        xsl_content = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <hrefs>
      <xsl:for-each select="//a/@href">
        <href><xsl:value-of select="."/></href>
      </xsl:for-each>
    </hrefs>
  </xsl:template>
</xsl:stylesheet>"""
        xml = '<?xml version="1.0"?><root><a href="https://example.com"/><a href="https://test.com"/></root>'
        result = run_xte_direct(xml.encode(), xsl_content.encode())
        assert "https://example.com" in result
        assert "https://test.com" in result

    def test_empty_result(self, tmp_path):
        xsl = tmp_path / "empty.xsl"
        xsl.write_text(
            """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result><xsl:value-of select="//nonexistent"/></result>
  </xsl:template>
</xsl:stylesheet>"""
        )
        result = run_xte(str(xsl), "<root/>")
        assert result.returncode == 0

    def test_empty_result_direct(self):
        """Direct function call for coverage."""
        xsl_content = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result><xsl:value-of select="//nonexistent"/></result>
  </xsl:template>
</xsl:stylesheet>"""
        result = run_xte_direct(b"<root/>", xsl_content.encode())
        assert "<result></result>" in result or "<result/>" in result

    def test_invalid_stylesheet_raises(self):
        """Test that invalid XSLT raises ValueError."""
        with pytest.raises(ValueError, match="Invalid XSLT"):
            transform_xml(b"<root/>", b"not valid xslt")

    def test_invalid_xml_raises(self):
        """Test that invalid XML raises ValueError."""
        xsl = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/"><xsl:text>test</xsl:text></xsl:template>
</xsl:stylesheet>"""
        with pytest.raises(ValueError, match="Invalid XML"):
            transform_xml(b"not valid xml", xsl.encode())


class TestXSLTParameters:
    def test_single_param(self):
        xsl = "<?xml version='1.0'?><xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'><xsl:template match='/'><out><xsl:value-of select='$myvar'/></out></xsl:template></xsl:stylesheet>"
        result = subprocess.run(
            XTE + ["-s", xsl, "-p", "myvar=hello"],
            input="<root/>",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_single_param_direct(self):
        """Direct function call for coverage."""
        xsl = "<?xml version='1.0'?><xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'><xsl:template match='/'><out><xsl:value-of select='$myvar'/></out></xsl:template></xsl:stylesheet>"
        params = {"myvar": etree.XSLT.strparam("hello")}
        result = run_xte_direct(b"<root/>", xsl.encode(), params)
        assert "hello" in result

    def test_multiple_params(self, tmp_path):
        xsl_file = tmp_path / "multi.xsl"
        xsl_file.write_text(
            """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <out><xsl:value-of select="concat($a, ' ', $b)"/></out>
  </xsl:template>
</xsl:stylesheet>"""
        )
        result = subprocess.run(
            XTE + [str(xsl_file), "-p", "a=hello", "-p", "b=world"],
            input="<root/>",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "hello world" in result.stdout

    def test_multiple_params_direct(self):
        """Direct function call for coverage."""
        xsl = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <out><xsl:value-of select="concat($a, ' ', $b)"/></out>
  </xsl:template>
</xsl:stylesheet>"""
        params = {
            "a": etree.XSLT.strparam("hello"),
            "b": etree.XSLT.strparam("world"),
        }
        result = run_xte_direct(b"<root/>", xsl.encode(), params)
        assert "hello world" in result

    def test_param_with_file_input(self, tmp_path):
        xsl_content = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result><xsl:value-of select="$greeting"/></result>
  </xsl:template>
</xsl:stylesheet>"""
        xsl_file = tmp_path / "param.xsl"
        xsl_file.write_text(xsl_content)
        xml_file = tmp_path / "input.xml"
        xml_file.write_text("<root/>")
        result = subprocess.run(
            XTE + [str(xsl_file), str(xml_file), "-p", "greeting=from_file"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "from_file" in result.stdout

    def test_parse_xslt_params(self):
        """Test XSLT parameter parsing."""
        params = parse_xslt_params(["a=hello", "b=world"])
        assert "a" in params
        assert "b" in params

    def test_parse_xslt_params_empty(self):
        """Test empty parameter list."""
        params = parse_xslt_params([])
        assert params == {}