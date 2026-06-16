import fitz  # PyMuPDF
from langchain_core.tools import tool
from matrixcurator.exceptions import DocumentParseError

@tool
def parse_with_pymupdf(file_content: bytes, filename: str) -> str:
    """Use this tool to parse PDF files using PyMuPDF. It is fast and works well for standard text-heavy PDFs."""
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        raise DocumentParseError(f"Failed to parse PDF with PyMuPDF: {str(e)}") from e
