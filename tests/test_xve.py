import subprocess
import sys
from typing import Optional

import pytest
from xve import load_schema, validate_xml

XVE = [sys.executable, "-m", "xve"]


def run_xve(schema_path, input_data=None):
    result = subprocess.run(
        XVE + [schema_path],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return result


def run_xve_direct(xml_data: bytes, xsd_data: bytes):
    """Direct function call for coverage."""
    schema = load_schema(xsd_data)
    return validate_xml(xml_data, schema)


@pytest.fixture
def simple_xsd(tmp_path):
    xsd = tmp_path / "simple.xsd"
    xsd.write_text(
        """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="item" type="xs:string" minOccurs="1" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""
    )
    return xsd


@pytest.fixture
def person_xsd(tmp_path):
    xsd = tmp_path / "person.xsd"
    xsd.write_text(
        """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="person">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="name" type="xs:string"/>
        <xs:element name="age" type="xs:integer"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""
    )
    return xsd


class TestValidValidation:
    def test_valid_xml(self, simple_xsd):
        xml = '<?xml version="1.0"?><root><item>Test</item></root>'
        result = run_xve(str(simple_xsd), xml)
        assert result.returncode == 0

    def test_valid_xml_direct(self, simple_xsd):
        """Direct function call for coverage."""
        xml = '<?xml version="1.0"?><root><item>Test</item></root>'
        result = run_xve_direct(xml.encode(), simple_xsd.read_bytes())
        assert result is True

    def test_multiple_items(self, simple_xsd):
        xml = '<?xml version="1.0"?><root><item>One</item><item>Two</item></root>'
        result = run_xve(str(simple_xsd), xml)
        assert result.returncode == 0

    def test_multiple_items_direct(self, simple_xsd):
        """Direct function call for coverage."""
        xml = '<?xml version="1.0"?><root><item>One</item><item>Two</item></root>'
        result = run_xve_direct(xml.encode(), simple_xsd.read_bytes())
        assert result is True

    def test_person_schema(self, person_xsd):
        xml = '<?xml version="1.0"?><person><name>John</name><age>30</age></person>'
        result = run_xve(str(person_xsd), xml)
        assert result.returncode == 0

    def test_person_schema_direct(self, person_xsd):
        """Direct function call for coverage."""
        xml = '<?xml version="1.0"?><person><name>John</name><age>30</age></person>'
        result = run_xve_direct(xml.encode(), person_xsd.read_bytes())
        assert result is True


class TestInvalidValidation:
    def test_invalid_xml(self, simple_xsd):
        xml = '<?xml version="1.0"?><wrongroot><item>Test</item></wrongroot>'
        result = run_xve(str(simple_xsd), xml)
        assert result.returncode == 2
        assert "validation failed" in result.stderr.lower()

    def test_invalid_xml_direct(self, simple_xsd):
        """Direct function call for coverage."""
        xml = '<?xml version="1.0"?><wrongroot><item>Test</item></wrongroot>'
        with pytest.raises(ValueError, match="validation failed"):
            run_xve_direct(xml.encode(), simple_xsd.read_bytes())

    def test_missing_required_element(self, person_xsd):
        xml = '<?xml version="1.0"?><person><name>John</name></person>'
        result = run_xve(str(person_xsd), xml)
        assert result.returncode == 2

    def test_missing_required_element_direct(self, person_xsd):
        """Direct function call for coverage."""
        xml = '<?xml version="1.0"?><person><name>John</name></person>'
        with pytest.raises(ValueError, match="validation failed"):
            run_xve_direct(xml.encode(), person_xsd.read_bytes())

    def test_wrong_element_order(self, person_xsd):
        xml = '<?xml version="1.0"?><person><age>30</age><name>John</name></person>'
        result = run_xve(str(person_xsd), xml)
        assert result.returncode == 2

    def test_wrong_element_order_direct(self, person_xsd):
        """Direct function call for coverage."""
        xml = '<?xml version="1.0"?><person><age>30</age><name>John</name></person>'
        with pytest.raises(ValueError, match="validation failed"):
            run_xve_direct(xml.encode(), person_xsd.read_bytes())

    def test_invalid_type(self, person_xsd):
        xml = '<?xml version="1.0"?><person><name>John</name><age>notanumber</age></person>'
        result = run_xve(str(person_xsd), xml)
        assert result.returncode == 2

    def test_invalid_type_direct(self, person_xsd):
        """Direct function call for coverage."""
        xml = '<?xml version="1.0"?><person><name>John</name><age>notanumber</age></person>'
        with pytest.raises(ValueError, match="validation failed"):
            run_xve_direct(xml.encode(), person_xsd.read_bytes())


class TestInputSources:
    def test_stdin_input(self, simple_xsd):
        xml = '<?xml version="1.0"?><root><item>From Stdin</item></root>'
        result = run_xve(str(simple_xsd), xml)
        assert result.returncode == 0

    def test_file_input(self, tmp_path, simple_xsd):
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><root><item>From File</item></root>')
        result = subprocess.run(
            XVE + [str(simple_xsd), str(xml_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestArgumentValidation:
    def test_missing_schema(self):
        result = subprocess.run(XVE + [], capture_output=True)
        assert result.returncode == 2

    def test_missing_input(self):
        xsd = '<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="root"/></xs:schema>'
        result = subprocess.run(XVE + ["-s", xsd], capture_output=True)
        assert result.returncode == 2

    def test_schema_not_found(self):
        result = subprocess.run(XVE + ["nonexistent.xsd"], capture_output=True)
        assert result.returncode == 2
        stderr = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
        assert "not found" in stderr.lower()

    def test_invalid_schema(self, tmp_path):
        invalid_xsd = tmp_path / "invalid.xsd"
        invalid_xsd.write_text("not valid xsd")
        result = subprocess.run(
            XVE + [str(invalid_xsd)],
            input="<root/>",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XSD" in result.stderr

    def test_invalid_schema_inline(self):
        result = subprocess.run(
            XVE + ["-s", "not valid xsd"],
            input="<root/>",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XSD" in result.stderr

    def test_invalid_schema_raises(self):
        """Test that invalid XSD raises ValueError."""
        with pytest.raises(ValueError, match="Invalid XSD"):
            load_schema(b"not valid xsd")

    def test_invalid_xml(self, simple_xsd):
        result = subprocess.run(
            XVE + [str(simple_xsd)],
            input="not valid xml",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XML" in result.stderr

    def test_invalid_xml_raises(self, simple_xsd):
        """Test that invalid XML raises ValueError."""
        schema = load_schema(simple_xsd.read_bytes())
        with pytest.raises(ValueError, match="Invalid XML"):
            validate_xml(b"not valid xml", schema)


class TestInlineSchema:
    def test_inline_schema(self):
        xsd = '<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="test"/></xs:schema>'
        xml = "<?xml version='1.0'?><test>Valid</test>"
        result = subprocess.run(
            XVE + ["-s", xsd],
            input=xml,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0