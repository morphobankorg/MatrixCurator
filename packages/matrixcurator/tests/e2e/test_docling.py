import pytest
import os
from matrixcurator.modules.tools.docling import parse_with_docling
from matrixcurator.exceptions import DocumentParseError

@pytest.mark.asyncio
async def test_parse_with_docling_missing_key(monkeypatch):
    """
    Test that the docling tool correctly bubbles up authentication errors 
    when no API key is provided, rather than failing silently or swallowing exceptions.
    """
    # Ensure no API keys are present in the environment for this test
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    
    # Use a real PDF fixture
    pdf_path = os.path.join(os.path.dirname(__file__), "data", "multi_page.pdf")
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    # LangChain's ainvoke might raise the error or return a ToolException string 
    # depending on tool config, but we raise DocumentParseError in the tool implementation.
    with pytest.raises(DocumentParseError) as exc_info:
        await parse_with_docling.ainvoke({
            "file_content": pdf_bytes, 
            "filename": "multi_page.pdf"
        })
    
    # Verify the error message contains indications of the failure
    assert "litellm.exceptions.AuthenticationError" in str(exc_info.value) or "Failed to parse document" in str(exc_info.value)


@pytest.mark.asyncio
async def test_parse_with_docling_success():
    """
    Test that the docling tool actually parses a PDF when an API key is available.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("No GEMINI_API_KEY available for E2E test")
        
    # Use a real PDF fixture
    pdf_path = os.path.join(os.path.dirname(__file__), "data", "multi_page.pdf")
    
    # Read the file contents
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    result = await parse_with_docling.ainvoke({
        "file_content": pdf_bytes, 
        "filename": "multi_page.pdf"
    })
    
    assert isinstance(result, str)
    assert len(result) > 10, f"Expected parsed text to have length > 10, but got: {result!r}"
