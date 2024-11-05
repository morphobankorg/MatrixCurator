from backend.apps.doc.utils import convert_pdf_to_markdown
from backend.apps.doc.utils import convert_docx_to_markdown


def convert_document_to_markdown(uploaded_file, page_range=None):
    """Converts a document (PDF or DOCX) to markdown based on file type and page range.

    Args:
        uploaded_file: The uploaded file object.
        page_range_string: An optional string representing the desired page range (e.g., '1-10', '5,12', '10').
                           If not provided, all pages will be converted.

    Returns:
        The converted markdown text, or None if an error occurs or the file type is unsupported.
    """
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]

        if file_extension == 'docx':
            return convert_docx_to_markdown(uploaded_file)
        elif file_extension == 'pdf':
            return convert_pdf_to_markdown(uploaded_file, page_range)
        else:
            print(f"Unsupported file type: {file_extension}")
            return None
    except Exception as e:
        print(f"Error converting document: {e}")
        return None