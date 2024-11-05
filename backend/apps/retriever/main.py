import re

def extract_numbers_with_index(text):
    """
    Extracts all whole numbers from a text string along with their indices.

    Args:
        text: The text string to search.

    Returns:
        A list of tuples, where each tuple contains a number and its starting index in the text.
    """

    numbers = []
    for match in re.finditer(r'\d+', text):
        numbers.append((int(match.group()), match.start()))
    return numbers

def order_numbers_by_occurrence(numbers_with_index, end_number):
    """
    Orders numbers from the input list based on their first occurrence, 
    following the sequence 1, 2, 3, ... and so on, ensuring that the index of a number is greater than 
    the index of the previous number.

    Args:
        numbers_with_index: A list of tuples, where each tuple contains a number and its starting index.

    Returns:
        A new list of tuples, ordered based on the first occurrence of each number, with increasing indices.
    """

    ordered_numbers = []
    seen_numbers = set()
    last_index = -1  # Initialize last_index to ensure the first number's index is valid
    for i in range(1, (end_number + 1)): 
        for number, index in numbers_with_index:
            if number == i and number not in seen_numbers and index > last_index:
                ordered_numbers.append((number, index))
                seen_numbers.add(number)
                last_index = index
                break

    return ordered_numbers

def extract_text_between_numbers(text, start_number, end_number, numbers_with_index, start_context_length=1000, end_context_length=1000):
    """
    Extracts the text between the first occurrences of two given numbers in a text string,
    including context before the start number and after the end number.

    Args:
        text: The text string to search.
        start_number: The starting number.
        end_number: The ending number.
        numbers_with_index: A list of tuples containing numbers and their indices from `extract_numbers_with_index`.
        context_length: The number of characters to include before and after the target numbers (default 500).

    Returns:
        The text between the two numbers, including context, or an empty string if either number is not found.
    """

    start_index = None
    end_index = None

    for number, index in numbers_with_index:
        if number == start_number and start_index is None:
            start_index = max(0, index - start_context_length)
        elif number == end_number and end_index is None:
            end_index = min(len(text), index + end_context_length)

    if start_index is not None and end_index is not None:
        return text[start_index:end_index]
    else:
        return text

def retrieve_context(text, start_number, end_number):
    numbers_with_index = extract_numbers_with_index(text)
    ordered_numbers = order_numbers_by_occurrence(numbers_with_index, end_number)

    extracted_text = extract_text_between_numbers(text, start_number, end_number, ordered_numbers)
    
    return extracted_text
    