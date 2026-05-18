import subprocess
import sys

import pytest

XVE = [sys.executable, "-m", "xve"]


def run_xve(schema_path, input_data=None):
    result = subprocess.run(
        XVE + [schema_path],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return result


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

    def test_multiple_items(self, simple_xsd):
        xml = '<?xml version="1.0"?><root><item>One</item><item>Two</item></root>'
        result = run_xve(str(simple_xsd), xml)
        assert result.returncode == 0

    def test_person_schema(self, person_xsd):
        xml = '<?xml version="1.0"?><person><name>John</name><age>30</age></person>'
        result = run_xve(str(person_xsd), xml)
        assert result.returncode == 0


class TestInvalidValidation:
    def test_invalid_xml(self, simple_xsd):
        xml = '<?xml version="1.0"?><wrongroot><item>Test</item></wrongroot>'
        result = run_xve(str(simple_xsd), xml)
        assert result.returncode == 2
        assert "validation failed" in result.stderr.lower()

    def test_missing_required_element(self, person_xsd):
        xml = '<?xml version="1.0"?><person><name>John</name></person>'
        result = run_xve(str(person_xsd), xml)
        assert result.returncode == 2

    def test_wrong_element_order(self, person_xsd):
        xml = '<?xml version="1.0"?><person><age>30</age><name>John</name></person>'
        result = run_xve(str(person_xsd), xml)
        assert result.returncode == 2

    def test_invalid_type(self, person_xsd):
        xml = '<?xml version="1.0"?><person><name>John</name><age>notanumber</age></person>'
        result = run_xve(str(person_xsd), xml)
        assert result.returncode == 2


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
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XSD" in result.stderr

    def test_invalid_schema_inline(self):
        result = subprocess.run(
            XVE + ["-s", "not valid xsd"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XSD" in result.stderr

    def test_invalid_xml(self, simple_xsd):
        result = subprocess.run(
            XVE + [str(simple_xsd)],
            input="not valid xml",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Invalid XML" in result.stderr


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