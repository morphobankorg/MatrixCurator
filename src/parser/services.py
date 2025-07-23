from io import StringIO
from typing import Union, BinaryIO, Any
import fitz
import docx
from .external_services import LlamaParseService
from .utils import PDFService, create_temp_file
from .exceptions import log_execution, handle_exceptions


class ParserService:

    def __init__(self, parser):
        self.parser = parser
        
    @log_execution
    @handle_exceptions
    def parse(self, file, pages: list) -> str:

        file_extension = "." + file.name.lower().split('.')[-1]

        if file_extension == ".pdf":
            pdf_service = PDFService()
            split_pdf = pdf_service.split_by_range(pdf_file=file, from_page=pages[0], to_page=pages[-1])

            if self.parser == "pyMuPDF":
                pymypdf_service = PyMuPDFService()
                return pymypdf_service.parse(pdf_file=split_pdf)
    
            elif self.parser == "llamaparse":
                split_pdf_path = create_temp_file(split_pdf, file_extension)
                llamaparse_service = LlamaParseService()
                return llamaparse_service.parse(split_pdf_path, file_extension)
            
            elif self.parser == "Gemini":
                return split_pdf
            
        elif file_extension == ".docx":
            
            if self.parser == "python-docx":
                docx_service = DocxService()
                return docx_service.parse(doc_file=file)
            
            elif self.parser == "Gemini":
                pdf_service = PDFService(pdf_file=file)
                return pdf_service.create_from_docx(doc_file=file, from_page=pages[0], to_page=pages[-1])
            
        elif file_extension == ".txt":
            return convert_txt_to_markdown(file)
            
class PyMuPDFService:

    def __init__(self) -> None:
        pass

    def parse_page(self, page: fitz.Page) -> str:
        """Extracts and formats text from a single PDF page.

        Args:
            page: A fitz.Page object representing the PDF page.

        Returns:
            A string containing the formatted text from the page.
        """
        page_text: str = ""
        blocks: list[Any] = page.get_text("blocks")
        
        for block in blocks:
            # Ignore empty or whitespace-only blocks
            if not block[4].strip():
                continue
            page_text += block[4].strip() + "\n"
        return page_text
    
    @log_execution
    @handle_exceptions
    def parse(self, pdf_file: Union[BinaryIO, bytes]) -> str:
        """Converts the entire PDF file to markdown text.

        Args:
            pdf_file: Either a file-like object in binary mode or raw bytes of the PDF.

        Returns:
            The converted markdown text as a string.

        Raises:
            Exception: If there's an error parsing the PDF document.
        """

        # Handle both file objects and raw bytes
        if isinstance(pdf_file, bytes):
            pdf_document = fitz.open(stream=pdf_file, filetype="pdf")
        else:
            # Ensure we're reading from the start of the file
            pdf_file.seek(0)
            pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        
        markdown_text: str = ""
        for page in pdf_document:
            markdown_text += self.parse_page(page)
        return markdown_text

class DocxService:
    def __init__(self) -> None:
        pass
    @log_execution
    def parse(self, doc_file: Union[BinaryIO, bytes]) -> str:
        """"
        Extracts text content from a .docx file.

        Args:
            doc_file (Union[BinaryIO, bytes]): The uploaded .docx file.

        Returns:
            str: The text content of the file.
        """
        # Load the docx file
        doc = docx.Document(doc_file)
        
        markdown_lines = []
        
        for paragraph in doc.paragraphs:
            text = paragraph.text
            
            # Check for headings
            if paragraph.style.name.startswith('Heading'):
                level = int(paragraph.style.name.split()[-1])
                markdown_lines.append(f"{'#' * level} {text}")
            else:
                # Check for lists
                if paragraph.style.name == 'List Paragraph':
                    # Assuming simple bullet lists
                    markdown_lines.append(f"- {text}")
                else:
                    # Regular paragraph
                    markdown_lines.append(text)
        
        # Join the lines into a single string
        markdown_text = "\n".join(markdown_lines)
        return markdown_text
@log_execution    
def convert_txt_to_markdown(uploaded_file):
    """
    Extracts text content from a .txt file uploaded via Streamlit.

    Args:
        uploaded_file (streamlit.runtime.uploaded_file_manager.UploadedFile): The uploaded .txt file.

    Returns:
        str: The text content of the file.  Returns an empty string if there's an error.
    """
    try:
        # Use StringIO to handle the UploadedFile like a file object
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))  # Decode assuming UTF-8 encoding

        # Read the entire content 
        text = stringio.read()
        return text

    except Exception as e:
        print(f"Error reading file: {e}")  #  Handle errors gracefully
        return ""  # or raise the exception if you want to stop execution