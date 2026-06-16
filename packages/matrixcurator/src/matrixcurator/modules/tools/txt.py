from langchain_core.tools import tool
from matrixcurator.exceptions import DocumentParseError

@tool
def parse_with_txt(file_content: bytes, filename: str) -> str:
    """Use this tool to parse plain text (TXT) files."""
    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return file_content.decode("latin-1")
        except Exception as e:
            raise DocumentParseError(f"Failed to parse TXT: {str(e)}") from e
    except Exception as e:
        raise DocumentParseError(f"Failed to parse TXT: {str(e)}") from e
