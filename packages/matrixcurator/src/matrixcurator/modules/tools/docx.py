import io
from langchain_core.tools import tool
from matrixcurator.exceptions import DocumentParseError

# Absolute import to avoid circular dependency with the file name
import docx as python_docx

@tool
def parse_with_docx(file_content: bytes, filename: str) -> str:
    """Use this tool to parse DOCX (Microsoft Word) files."""
    try:
        doc = python_docx.Document(io.BytesIO(file_content))
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return "\n".join(text)
    except Exception as e:
        raise DocumentParseError(f"Failed to parse DOCX: {str(e)}") from e
