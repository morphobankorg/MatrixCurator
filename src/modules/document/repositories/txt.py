from src.exceptions import DocumentParseError

def read_txt(file_content: bytes, **kwargs) -> str:
    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return file_content.decode("latin-1")
        except Exception as e:
            raise DocumentParseError(f"Failed to parse TXT: {str(e)}") from e
    except Exception as e:
        raise DocumentParseError(f"Failed to parse TXT: {str(e)}") from e
