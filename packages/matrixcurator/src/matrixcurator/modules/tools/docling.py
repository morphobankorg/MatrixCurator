import io
from langchain_core.tools import tool
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from matrixcurator.exceptions import DocumentParseError

@tool
def parse_with_docling(file_content: bytes, filename: str) -> str:
    """Use this tool to parse complex documents (PDF, DOCX, HTML, etc.) using Docling. It is slower but highly accurate for complex layouts, tables, and reading order."""
    try:
        buf = io.BytesIO(file_content)
        stream = DocumentStream(name=filename, stream=buf)
        converter = DocumentConverter()
        result = converter.convert(stream)
        return result.document.export_to_markdown()
    except Exception as e:
        raise DocumentParseError(f"Failed to parse document with Docling: {str(e)}") from e
