from lxml import etree

def parse_xml(generated_response):
    """
    Processes a list of items from the generated response and returns a list of XML character state labels.

    Args:
        generated_response: A list of items from the generated response.

    Returns:
        A list of XML character state labels, or an empty list if there are no items.

    Raises:
        ValueError: If any item in the generated response cannot be repaired and parsed.
    """

    xml_characterstateslabels = []
    for item in generated_response:
        try:
            xml_bytes = trim_repair(item)
            xml_characterstateslabels.append(xml_bytes)
        except Exception as e:
            # Handle potential errors during repair and parsing, e.g., log the error
            xml_characterstateslabels.append("")

    return xml_characterstateslabels

def trim_repair(data):

    # Find the start and end positions of the XML within the text data
    start_index = data.find("<characters>")
    end_index = data.find("</characters>", start_index) + len("</characters>")

    if start_index == -1 or end_index == -1:
        raise ValueError("Invalid input: Couldn't find XML data within the text.")
    
    
    xml_data = data[start_index:end_index]

    xml_data = xml_data.replace(""""><""", """">&lt;""")
    xml_data = xml_data.replace("""">>""", """">&gt;""")
    xml_data = xml_data.replace(""""> <""", """">&lt;""")
    xml_data = xml_data.replace(""""> >""", """">&gt;""")
    xml_data = xml_data.replace("≤", "&lt;=")
    xml_data = xml_data.replace("≥", "&gt;=")
    
    xml = etree.fromstring(xml_data.encode('utf-8'))
    xml_bytes = etree.tostring(xml)
    return xml_bytes

def check_count_and_range(xml_tree, start_index, end_index):
    """
    Validates the XML data according to the specified criteria.

    Args:
        xml_data (str): The XML data as a string.
        start_index (int): The starting index.
        end_index (int): The ending index.

    Returns:
        bool: True if the XML data is valid, False otherwise.
    """

    try:
        tree = etree.fromstring(xml_tree)
    except etree.XMLSyntaxError as e:
        return False

    root = tree

    # 1. Check for non-empty 'name' attributes
    for character in root.iter('character'):
        if not character.attrib.get('name'):
            print(f"Error: Character at index {character.attrib['index']} is missing 'name' attribute.")
            return False

    # 2. Check index range and presence of each index
    expected_indices = set(range(start_index, end_index + 1))
    found_indices = set()

    for character in root.iter('character'):
        index = int(character.attrib['index'])
        if index in found_indices:
            print(f"Error: Duplicate character index {index} found.")
            return False
        elif index not in expected_indices:
            print(f"Error: Character index {index} is out of range ({start_index}-{end_index}).")
            return False
        found_indices.add(index)

    if found_indices != expected_indices:
        missing_indices = expected_indices - found_indices
        print(f"Error: Missing characters with indices: {missing_indices}")
        return False

    return True  # All validations passed

def validate_xml(column_dict, xml_list):
    
    validation_list = []

    for i in range(len(column_dict)):
        start = column_dict[i]['start']
        end = column_dict[i]['end']

        xml_character = xml_list[i]

        status = check_count_and_range(xml_character, start, end)
        if status == True:
            value = 1
            validation_list.append(value)
        elif status == False:
            value = 0 
            validation_list.append(value)

    return validation_list

def build_character_state_labels(xml_tree):
    """
    Extracts CHARSTATELABELS from the provided XML tree, formatted as specified,
    prioritizing the 'index' attribute for character numbering.

    Args:
        xml_tree: The parsed XML tree.

    Returns:
        list: List of formatted CHARSTATELABELS strings.
    """

    tree = etree.ElementTree(xml_tree)
    root = tree.getroot()

    character_state_labels = []

    for character in root.findall("character"):
        name = character.attrib["name"].replace("'", "?")

        # Prioritize 'index' attribute if it exists
        if 'index' in character.attrib:
            character_number = int(character.attrib['index'])
        else:
            character_number = len(character_state_labels) + 1  # Fallback: sequential numbering

        states = ["'" + state.text + "'" for state in character.findall("state")]
        label = f"{character_number} '{name}' / {' '.join(states)},"

        character_state_labels.append("\t\t" + label)

    character_state_labels[-1] = character_state_labels[-1].replace(",", ";")

    return character_state_labels