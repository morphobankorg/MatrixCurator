import pytest
from unittest.mock import patch
from matrixcurator.modules.document.services import parse_document, generate_document
from matrixcurator.exceptions import DocumentParseError

@patch("matrixcurator.modules.document.services.read_pdf")
def test_document_service_parse_pdf(mock_read_pdf):
    mock_read_pdf.return_value = "mocked pdf read"
    result = parse_document(b"test", "test.pdf")
    assert result == "mocked pdf read"
    mock_read_pdf.assert_called_once_with(b"test")

@patch("matrixcurator.modules.document.services.read_docx")
def test_document_service_parse_docx(mock_read_docx):
    mock_read_docx.return_value = "mocked docx read"
    result = parse_document(b"test", "test.docx")
    assert result == "mocked docx read"
    mock_read_docx.assert_called_once_with(b"test")

@patch("matrixcurator.modules.document.services.read_txt")
def test_document_service_parse_txt(mock_read_txt):
    mock_read_txt.return_value = "mocked txt read"
    result = parse_document(b"test", "test.txt")
    assert result == "mocked txt read"
    mock_read_txt.assert_called_once_with(b"test")

def test_document_service_parse_unsupported():
    with pytest.raises(DocumentParseError) as exc_info:
        parse_document(b"test", "test.png")
    assert "Unsupported file type" in str(exc_info.value)

@patch("matrixcurator.modules.document.services.write_nexus")
def test_document_service_generate(mock_write_nexus):
    mock_write_nexus.return_value = b"mocked write"
    result = generate_document("original", [{"test": "data"}])
    assert result == b"mocked write"
    mock_write_nexus.assert_called_once_with("original", [{"test": "data"}])
