# src/parser/utils.py

import tempfile
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from typing import Union
# REMOVE: from docx2pdf import convert
import subprocess  # ADD THIS
import os          # ADD THIS
from .exceptions import log_execution, handle_exceptions

@log_execution
@handle_exceptions
def create_temp_file(file: Union[bytes, BytesIO], file_extention: str) -> str:
    """Creates a temporary file with the given document content and suffix."""
    if not isinstance(file, (bytes, BytesIO)):
        raise TypeError("Document must be bytes or BytesIO")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extention) as temp_file:
        if isinstance(file, bytes):
            temp_file.write(file)
        else:
            temp_file.write(file.getvalue())
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
            pdf_file.seek(0)  # Ensure we read from the beginning
            return PdfReader(pdf_file)
        else:
            raise TypeError("PDF content must be bytes or BytesIO")

    @log_execution
    @handle_exceptions
    def split_by_range(self, pdf_file: Union[bytes, BytesIO], from_page: int, to_page: int) -> BytesIO:
        """Extracts a range of pages from a PDF."""
        try:
            pdf_file_reader = self._pdf_file_reader(pdf_file)
            total_pages = len(pdf_file_reader.pages)

            if from_page < 0 or from_page >= total_pages or to_page < 0 or to_page >= total_pages or from_page > to_page:
                # If range is invalid, just return the original full PDF content
                if isinstance(pdf_file, BytesIO):
                    pdf_file.seek(0)
                    return pdf_file
                return BytesIO(pdf_file)

            pdf_writer = PdfWriter()
            for i in range(from_page, to_page + 1):
                pdf_writer.add_page(pdf_file_reader.pages[i])

            output_pdf_buffer = BytesIO()
            pdf_writer.write(output_pdf_buffer)
            output_pdf_buffer.seek(0)
            return output_pdf_buffer
        except Exception:
            if isinstance(pdf_file, BytesIO):
                pdf_file.seek(0)
                return pdf_file
            return BytesIO(pdf_file)
    
    @log_execution
    @handle_exceptions
    def create_from_docx(self, doc_file: Union[bytes, BytesIO], from_page: int, to_page: int) -> BytesIO:
        """Converts a DOCX file to PDF using LibreOffice headless mode."""
        
        temp_docx_path = None
        try:
            # Create a temporary directory to store the output PDF
            with tempfile.TemporaryDirectory() as output_dir:
                # 1. Create a temporary DOCX file from the in-memory object
                temp_docx_path = create_temp_file(doc_file, ".docx")

                # 2. Run the LibreOffice conversion command
                subprocess.run(
                    [
                        "libreoffice",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        output_dir,
                        temp_docx_path,
                    ],
                    check=True,  # Raise an exception if the command fails
                    capture_output=True, # Capture stdout/stderr for debugging
                    text=True
                )

                # 3. Construct the path to the converted PDF
                pdf_filename = os.path.splitext(os.path.basename(temp_docx_path))[0] + ".pdf"
                temp_pdf_path = os.path.join(output_dir, pdf_filename)

                # 4. Read the converted PDF file back into bytes
                with open(temp_pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
        
        except subprocess.CalledProcessError as e:
            raise  # Re-raise the exception to be handled by the app
        
        finally:
            # 5. Clean up the temporary input DOCX file
            if temp_docx_path and os.path.exists(temp_docx_path):
                os.remove(temp_docx_path)

        # 6. Proceed with splitting the converted PDF
        split_pdf = self.split_by_range(pdf_file=pdf_bytes, from_page=from_page, to_page=to_page)
        return split_pdf