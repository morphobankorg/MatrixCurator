import tempfile
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from typing import Union
from docx2pdf import convert
from .exceptions import log_execution, handle_exceptions

@log_execution
@handle_exceptions
def create_temp_file(file: Union[bytes, BytesIO], file_extention: str) -> str:
    """Creates a temporary file with the given document content and suffix.

    Args:
        file: The document content as bytes or a BytesIO object.
        file_extention: The file suffix (e.g., ".pdf", ".docx").

    Returns:
        The path to the temporary file.
        Raises TypeError if the document is not bytes or BytesIO.

    """
    if not isinstance(file, (bytes, BytesIO)):
        raise TypeError("Document must be bytes or BytesIO")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extention) as temp_file:
        if isinstance(file, bytes):
            temp_file.write(file)
        else: # it's a BytesIO object
            temp_file.write(file.getvalue())  # Get the bytes from BytesIO
        temp_path = temp_file.name
    return temp_path


class PDFService:
    def __init__(self):
        pass
    @log_execution
    @handle_exceptions
    def _pdf_file_reader(self, pdf_file: Union[bytes, BytesIO]) -> PdfReader:
        """Helper method to initialize the PDF reader"""
        if isinstance(pdf_file, bytes):
            return PdfReader(BytesIO(pdf_file))
        elif isinstance(pdf_file, BytesIO):
            return PdfReader(pdf_file)
        else:
            raise TypeError("PDF content must be bytes or BytesIO")

    @log_execution
    @handle_exceptions
    def split_by_range(self, pdf_file: Union[bytes, BytesIO], from_page: int, to_page: int) -> BytesIO:
        """
        Extracts a range of pages from a PDF, creating a new PDF containing only those pages.

        Args:
            from_page: The starting page number (0-indexed, inclusive)
            to_page: The ending page number (0-indexed, inclusive)

        Returns:
            - A BytesIO object containing the extracted PDF pages
        """
        # Exceptions Decorator
        try:

            pdf_file_reader = self._pdf_file_reader(pdf_file)
            
            total_pages = len(pdf_file_reader.pages)

            # Validate page range
            if from_page < 0 or from_page >= total_pages:
                raise ValueError(
                    f"Invalid starting page: {from_page}. Pages are 0-indexed and must be less than {total_pages}"
                )
            if to_page < 0 or to_page >= total_pages:
                raise ValueError(
                    f"Invalid ending page: {to_page}. Pages are 0-indexed and must be less than {total_pages}"
                )
            if from_page > to_page:
                raise ValueError(
                    f"Invalid page range: starting page ({from_page}) cannot be greater than ending page ({to_page})"
                )

            pdf_writer = PdfWriter()

            for i in range(from_page, to_page + 1):
                pdf_writer.add_page(pdf_file_reader.pages[i])

            output_pdf_buffer = BytesIO()
            pdf_writer.write(output_pdf_buffer)
            output_pdf_buffer.seek(0)

            return output_pdf_buffer
        
        except:
            return pdf_file
        
    @log_execution
    @handle_exceptions
    def create_from_docx(self, doc_file: Union[bytes, BytesIO], from_page: int, to_page: int) -> BytesIO:
        pdf_file = convert(doc_file)
        split_pdf = self.split_by_range(pdf_file=pdf_file, from_page=from_page, to_page=to_page)
        return split_pdf

