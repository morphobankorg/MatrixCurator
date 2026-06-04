# src/modules/document/services.py
from typing import Any, Dict, List
from matrixcurator.modules.document.repositories.pdf import read_pdf
from matrixcurator.modules.document.repositories.docx import read_docx
from matrixcurator.modules.document.repositories.txt import read_txt
from matrixcurator.modules.document.repositories.nexus import write_nexus
from matrixcurator.exceptions import DocumentParseError

def parse_document(file_content: bytes, filename: str, **kwargs) -> str:
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return read_pdf(file_content, **kwargs)
    elif filename.endswith(".docx"):
        return read_docx(file_content, **kwargs)
    elif filename.endswith(".txt"):
        return read_txt(file_content, **kwargs)
    else:
        raise DocumentParseError("Unsupported file type")

def generate_document(original_nexus: str, extracted_states: List[Dict[str, Any]], **kwargs) -> bytes:
    return write_nexus(original_nexus, extracted_states, **kwargs)

