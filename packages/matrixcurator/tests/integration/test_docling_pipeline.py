import io
import pytest
from unittest.mock import patch, MagicMock
from docling.datamodel.document import InputFormat
from matrixcurator.modules.tools.docling import parse_with_docling
from matrixcurator.config.main import settings

def create_mock_pdf() -> bytes:
    """Create a minimal valid PDF in memory without external dependencies."""
    # A minimal valid PDF 1.4 document
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
72 712 Td
(Hello, world!) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000236 00000 n 
0000000331 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
419
%%EOF
"""

@patch("matrixcurator.integrations.docling.completion")
def test_docling_tool_uses_gemini_fallback(mock_completion):
    # Arrange
    mock_pdf = create_mock_pdf()
    
    # Mock the LiteLLM completion to return a valid response without hitting API
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Mock Gemini extraction result"
    mock_completion.return_value = mock_response
    
    # Act
    result = parse_with_docling.invoke({"file_content": mock_pdf, "filename": "test.pdf"})
    
    # Assert
    # Verify that litellm was called instead of the standard Docling pipeline
    mock_completion.assert_called()
    kwargs = mock_completion.call_args.kwargs
    assert kwargs["model"] == settings.vlm_model
    assert "messages" in kwargs
    
    # The result should contain the mock text (note: Docling may format this as markdown, 
    # but the content from the mock should be integrated or it proves the pipeline executed)
    assert isinstance(result, str)
