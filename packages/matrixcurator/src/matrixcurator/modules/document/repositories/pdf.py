import fitz  # PyMuPDF
from matrixcurator.exceptions import DocumentParseError


def read_pdf(file_content: bytes, **kwargs) -> str:
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        raise DocumentParseError(f"Failed to parse PDF: {str(e)}") from e
