import tempfile
from io import BytesIO
import os

import streamlit as st

from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
import fitz
import re
import docx

from PyPDF2 import PdfReader, PdfWriter


LLAMACLOUD_API_KEY=st.secrets.llamacloud.api_key


def extract_text_from_pdf_page(page):
    """Extracts and formats text from a single PDF page.

    Args:
        page: A fitz.Page object representing the PDF page.

    Returns:
        A string containing the formatted text from the page.
    """
    page_text = ""
    for block in page.get_text("blocks"):
        # Ignore empty or whitespace-only blocks
        if not block[4].strip():
            continue
        page_text += block[4].strip() + "\n"
    return page_text

def parse_page_range_string(page_range_string):
    """Parses a string representing a page range into a list of page numbers.
    
    Args:
        page_range_string: A string representing the page range 
                           (e.g., '1-10', '5,12', '10').

    Returns:
        A list of integers representing the page numbers in the range.

    Raises:
        ValueError: If the input string is not a valid page range.
    """
    match = re.search(r"^\s*(\d+)\s*([-,\s]+\s*(\d+)\s*)?$", page_range_string)
    if match:
        start_page = int(match.group(1))
        end_page = int(match.group(3)) if match.group(3) else start_page
        if start_page <= end_page:
            return list(range(start_page - 1, end_page))
        else:
            raise ValueError("Invalid page range: start page must be less than or equal to end page.")
    else:
        raise ValueError("Invalid page range format.")


def convert_docx_to_markdown(doc_file):
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
    
def convert_pdf_to_markdown(pdf_file, pages):
    """Converts specific pages of a PDF file to markdown text.

    Args:
        pdf_file: The PDF file object.
        pages: A list of integers representing the desired page numbers.

    Returns:
        The converted markdown text as a string.
    """
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        markdown_text = ""
        for page_num in pages:
            page = pdf_document[page_num]
            markdown_text += extract_text_from_pdf_page(page)
        return markdown_text
    except Exception as e:
        raise Exception(f"Error parsing PDF document: {e}")

def create_temp_file(document, suffix):
    """Creates a temporary file with the given document content and suffix.

    Args:
        document: The document content as bytes or a BytesIO object.
        suffix: The file suffix (e.g., ".pdf", ".docx").

    Returns:
        The path to the temporary file.
        Raises TypeError if the document is not bytes or BytesIO.

    """
    if not isinstance(document, (bytes, BytesIO)):
        raise TypeError("Document must be bytes or BytesIO")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        if isinstance(document, bytes):
            temp_file.write(document)
        else: # it's a BytesIO object
            temp_file.write(document.getvalue())  # Get the bytes from BytesIO
        temp_path = temp_file.name
    return temp_path


def _llamaparse_worker(temp_file, file_extension=None):
    """
    Uses LlamaParse to parse a given file and returns the parsed markdown text.

    Args:
        temp_file (str): Path to the document file.
        file_extension (str, optional): File extension. Defaults to None.

    Returns:
        list: A list of strings, where each string represents the parsed content of a page.
          Returns an empty list on error.
    """
    if not file_extension:
        file_extension = os.path.splitext(temp_file)[1].lower()

    parser = LlamaParse(result_type="markdown", api_key=LLAMACLOUD_API_KEY)
    file_extractor = {file_extension: parser}

    try:
        documents = SimpleDirectoryReader(
            input_files=[temp_file], file_extractor=file_extractor
        ).load_data()
        return [doc.text for doc in documents]
    except Exception as e:
        print(f"Error loading document: {e}")
        return []


def parse_with_llamaparse(uploaded_file, pages=None, file_extension=None):
    """
    Extracts and concatenates specified pages from a document by leveraging the llamaparse_worker.

    Args:
        temp_file (str): Path to the document file.
        pages (list, optional): List of page numbers to extract (0-indexed). Defaults to None.
        file_extension (str, optional): File extension. Defaults to None.

    Returns:
        str: Concatenated content of the extracted pages.  Returns an empty string if there's an error or no pages are parsed.
    """

    if file_extension == '.pdf':
        
        uploaded_file, pages = extract_pdf_pages(uploaded_file, pages)

    temp_file = create_temp_file(uploaded_file, suffix=file_extension) 

    parsed_pages = _llamaparse_worker(temp_file, file_extension)

    if not parsed_pages:
        return ""  # Handle the case where llamaparse_worker returns an empty list due to error

    extracted_pages = []
    if pages:
        try:
            for page_num in pages:
                extracted_pages.append(parsed_pages[page_num])
        except IndexError as e:  # Only catch IndexError, TypeError shouldn't occur anymore
            print(f"Error extracting specific pages: {e}. Extracting all pages instead.")
            extracted_pages = parsed_pages  # Fallback to all pages
    else:
        extracted_pages = parsed_pages

    concatenated_content = "".join(extracted_pages)
    return concatenated_content

def extract_pdf_pages(pdf_content, page_numbers):
    """
    Extracts specific pages from a PDF, creating a new PDF containing only those pages.

    Args:
        pdf_content: The PDF content as bytes or a BytesIO object.
        page_numbers: A list of 0-indexed page numbers to include in the new PDF.

    Returns:
        A tuple containing:
            - A BytesIO object containing the extracted PDF pages.
            - A list of the new page numbers (always starting from 0).

    Raises:
        ValueError: If `page_numbers` contains invalid page numbers.
        TypeError: If `pdf_content` is not bytes or BytesIO.
    """
    try:
        if isinstance(pdf_content, bytes):
            pdf_reader = PdfReader(BytesIO(pdf_content))
        elif isinstance(pdf_content, BytesIO):
            pdf_reader = PdfReader(pdf_content)
        else:
            raise TypeError("pdf_content must be bytes or BytesIO")

        total_pages = len(pdf_reader.pages)

        # Validate page numbers
        for page_number in page_numbers:
            if page_number < 0 or page_number >= total_pages:
                raise ValueError(
                    f"Invalid page number: {page_number}. Pages are 0-indexed and must be less than {total_pages}"
                )

        pdf_writer = PdfWriter()
        extracted_page_numbers = []

        for i, page_number in enumerate(page_numbers):
            pdf_writer.add_page(pdf_reader.pages[page_number])
            extracted_page_numbers.append(i)

        output_pdf_buffer = BytesIO()
        pdf_writer.write(output_pdf_buffer)
        output_pdf_buffer.seek(0)

        return output_pdf_buffer, extracted_page_numbers

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None  # Or raise the exception if you prefer