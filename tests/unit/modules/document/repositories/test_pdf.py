import pytest
from unittest.mock import patch, MagicMock
from src.modules.document.repositories.pdf import read_pdf
from src.exceptions import DocumentParseError

@patch("src.modules.document.repositories.pdf.fitz.open")
def test_pdf_repository_read_success(mock_fitz_open):
    # Arrange
    mock_doc = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Page 1 text. "
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Page 2 text."
    
    # Make the mock document iterable
    mock_doc.__iter__.return_value = [mock_page1, mock_page2]
    mock_fitz_open.return_value = mock_doc
    
    content = b"fake pdf content"
    
    # Act
    result = read_pdf(content)
    
    # Assert
    assert result == "Page 1 text. Page 2 text."
    mock_fitz_open.assert_called_once_with(stream=content, filetype="pdf")

@patch("src.modules.document.repositories.pdf.fitz.open")
def test_pdf_repository_read_failure(mock_fitz_open):
    # Arrange
    mock_fitz_open.side_effect = Exception("Corrupted PDF")
    content = b"corrupted pdf content"
    
    # Act & Assert
    with pytest.raises(DocumentParseError) as exc_info:
        read_pdf(content)
    
    assert "Failed to parse PDF: Corrupted PDF" in str(exc_info.value)
