import io
from unittest.mock import patch

import pytest

from common import read_input, read_content_or_file


class TestReadInput:
    def test_read_from_file(self, tmp_path):
        test_file = tmp_path / "test.xml"
        test_file.write_text("<root>Test</root>")
        
        result = read_input(None, str(test_file))
        assert result == b"<root>Test</root>"

    def test_read_from_stdin(self):
        mock_stdin = type('obj', (object,), {'buffer': io.BytesIO(b"<root>From stdin</root>")})()
        
        result = read_input(mock_stdin)
        assert result == b"<root>From stdin</root>"


class TestReadContentOrFile:
    def test_inline_content(self):
        class MockParser:
            def error(self, msg):
                raise ValueError(msg)
        
        parser = MockParser()
        result = read_content_or_file(parser, "test content", "dummy.xsl", True, "Test")
        assert result == b"test content"

    def test_file_content(self, tmp_path):
        class MockParser:
            def error(self, msg):
                raise ValueError(msg)
        
        test_file = tmp_path / "test.xsl"
        test_file.write_text("XSL content")
        
        parser = MockParser()
        result = read_content_or_file(parser, "", str(test_file), False, "Test")
        assert result == b"XSL content"

    def test_file_not_found(self, tmp_path):
        class MockParser:
            def error(self, msg):
                raise ValueError(msg)
        
        parser = MockParser()
        with pytest.raises(ValueError, match="not found"):
            read_content_or_file(parser, "", "nonexistent.xsl", False, "Test")

    def test_permission_error(self, tmp_path):
        class MockParser:
            def error(self, msg):
                raise ValueError(msg)
        
        test_file = tmp_path / "test.xsl"
        test_file.write_text("content")
        
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            parser = MockParser()
            with pytest.raises(ValueError, match="Cannot read"):
                read_content_or_file(parser, "", str(test_file), False, "Test")
