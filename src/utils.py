import re

def parse_page_range_string(page_range_string: str | None):
    """Parses a string representing a page range into a list of page numbers.
    
    Args:
        page_range_string: A string representing the page range 
                           (e.g., '1-10', '5,12', '10').

    Returns:
        A list of integers representing the page numbers in the range.

    Raises:
        ValueError: If the input string is not a valid page range.
    """
    if not page_range_string:
        return []
    match = re.search(r"^\s*(\d+)\s*([-,\s]+\s*(\d+)\s*)?$", page_range_string)
    if match:
        start_page = int(match.group(1))
        end_page = int(match.group(3)) if match.group(3) else start_page
        if start_page <= end_page:
            return list(range(start_page - 1, end_page))
        else:
            raise ValueError("Invalid page range: start page must be less than or equal to end page.")
    else:
        []