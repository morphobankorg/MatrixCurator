# src/modules/document/repositories/docx.py
import docx
import io
from matrixcurator.exceptions import DocumentParseError


def read_docx(file_content: bytes, **kwargs) -> str:
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return "\n".join(text)
    except Exception as e:
        raise DocumentParseError(f"Failed to parse DOCX: {str(e)}") from e
