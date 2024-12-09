from backend.apps.doc.utils import convert_pdf_to_markdown, convert_txt_to_markdown, convert_docx_to_markdown, parse_with_llamaparse

def convert_document_to_markdown(uploaded_file, pages=None, parser='llamaparse'):
    """Converts a document (PDF or DOCX) to markdown based on file type and page range.

    Args:
        uploaded_file: The uploaded file object.
        pages: pages: A list of integers representing the desired page numbers. If not provided, all pages will be converted.

    Returns:
        The converted markdown text, or None if an error occurs or the file type is unsupported.
    """
    try:
        file_extension = "." + uploaded_file.name.lower().split('.')[-1]

        if parser == "plain-txt":
            return convert_txt_to_markdown(uploaded_file)
        elif parser == "llamaparse":
            return parse_with_llamaparse(uploaded_file, pages=pages, file_extension=file_extension)
        elif file_extension == ".docx" and parser == "python-docx":
            return convert_docx_to_markdown(uploaded_file)
        elif file_extension == ".pdf" and parser == "pyMuPDF":
            return convert_pdf_to_markdown(uploaded_file, pages=pages)
        else:
            print(f"Unsupported file type: {file_extension}")
            return None
        
    except Exception as e:
        print(f"Error converting document: {e}")
        return None
    
