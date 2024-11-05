import fitz
import re
import docx

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
    
def convert_pdf_to_markdown(pdf_file, page_numbers):
    """Converts specific pages of a PDF file to markdown text.

    Args:
        pdf_file: The PDF file object.
        page_numbers: A list of integers representing the desired page numbers.

    Returns:
        The converted markdown text as a string.
    """
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        markdown_text = ""
        for page_num in page_numbers:
            page = pdf_document[page_num]
            markdown_text += extract_text_from_pdf_page(page)
        return markdown_text
    except Exception as e:
        raise Exception(f"Error parsing PDF document: {e}")