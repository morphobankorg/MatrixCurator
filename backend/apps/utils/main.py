import re

def get_sanitized_filename(filename):
    """
    Cleans a filename for safe use with Python and SQLite3 and adds "mb_" prefix.

    Args:
        filename: The filename to be cleaned.

    Returns:
        A cleaned filename with "mb_" prefix, special characters removed,
        and spaces replaced with underscores.
    """

    # Delete numbers with brackets around it
    cleaned_filename = re.sub(r"\(\d\)", "", filename)

    # Remove all non-alphanumeric characters and underscores
    cleaned_filename = re.sub(r'[^\w_]', '_', cleaned_filename)

    # Replace multiple underscores with a single underscore
    cleaned_filename = re.sub(r'_+', '_', cleaned_filename)

    # Strip trailing underscore (if any)
    cleaned_filename = cleaned_filename.rstrip("_")

    # Add "mb_" prefix to the filename
    cleaned_filename = "sj_" + cleaned_filename + "_mb"

    return cleaned_filename.lower()  # Convert to lowercase for consistency