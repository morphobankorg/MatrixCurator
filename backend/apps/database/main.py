import sys
sys.path.append('../backend')

import sqlite3
import os
from lxml import etree

from backend.apps.retriever.main import retrieve_context
from backend.static.prompt_template import generative_prompt

DATA_DIR = os.path.dirname(__file__) + "/../../data"
BATCH_SIZE = 10

def initialize_database(table_name, raw_characters, total_characters):
    """
    Creates a table with the specified name in the SQLite database,
    emptying it if it already exists.

    Args:
        table_name (str): The name of the table to create or empty.
    """
    conn = sqlite3.connect(f"{DATA_DIR}/app.db")  # Connect to the database
    cursor = conn.cursor()

    # Drop the table if it already exists
    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")

    # Create the table
    cursor.execute(f"""
        CREATE TABLE {table_name} (
            start INTEGER,
            end INTEGER,
            context TEXT,
            prompt TEXT,
            xml_characters BLOB,
            validation_status BOOLEAN DEFAULT FALSE,
            evaluation_status BOOLEAN DEFAULT FALSE
        );
    """)

    start = 1
    while start <= total_characters:
        end = min(start + BATCH_SIZE - 1, total_characters)

        context = retrieve_context(raw_characters, start, end)
        prompt = generative_prompt.format(start=start, end=end)

        cursor.execute(f"""
            INSERT INTO {table_name} (start, end, context, prompt)
            VALUES (?, ?, ?, ?)
        """, (start, end, context, prompt))
        conn.commit()

        start = end + 1

    conn.commit()
    conn.close()  # Close the connection to the database


def identify_invalid_batches(table_name):
    """
    Fetches a list of question IDs with validation status False from the specified table.
    Also identifies empty entries in the "xml_characters" column.

    Args:
        table_name (str): The name of the table in the database.

    Returns:
        list: A list of question IDs with validation status False or empty "xml_characters" entries.
    """
    characters_dict = []
    conn = sqlite3.connect(f"{DATA_DIR}/app.db")  # Connect to the SQLite database

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT start, end, xml_characters
        FROM {table_name}
        WHERE validation_status != 1 OR evaluation_status != 1 OR xml_characters IS NULL OR xml_characters = '';
    """)

    for row in cursor.fetchall():
        characters = {"start": row[0],"end": row[1]}
        characters_dict.append(characters)

    conn.close()  # Close the connection to the database

    return characters_dict

def update_database(table_name, column_dict, data_list, column_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(f"{DATA_DIR}/app.db")
    cursor = conn.cursor()

    # Iterate over the dictionaries and xml_list
    for i in range(len(column_dict)):
        # Get the start and end values from the dictionary
        start = column_dict[i]['start']
        end = column_dict[i]['end']

        # Get the xml_character from the xml_list
        xml_character = data_list[i]

        # Update the row in the table
        cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE start = ? AND end = ?", (xml_character, start, end))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

import sqlite3

def read_database(table_name, column_dicts, column_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(f"{DATA_DIR}/app.db")
    cursor = conn.cursor()

    # Prepare a list to hold all the values
    all_values = []

    # Iterate over each dictionary in the list
    for column_dict in column_dicts:
        # Get the start and end values from the dictionary
        start = column_dict['start']
        end = column_dict['end']

        # Execute the SELECT statement
        cursor.execute(f"SELECT {column_name} FROM {table_name} WHERE start = ? AND end = ?", (start, end))

        # Fetch all the rows
        rows = cursor.fetchall()

        # Extract the values from the specified column and add them to the list
        all_values.extend([row[0] for row in rows])

    # Close the connection
    conn.close()

    # Return the list of values from the specified column
    return all_values

def get_labels(table_name, column_name='xml_characters'):

    # Connect to the SQLite database
    conn = sqlite3.connect(f"{DATA_DIR}/app.db")
    cursor = conn.cursor()

    # Prepare a list to hold all the values
    all_values = etree.Element('characters')

    # Use parameterized query to prevent SQL injection
    cursor.execute(f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL AND {column_name} <> ''")
    
    rows = cursor.fetchall()

    # Parse each XML string and append it to the all_values element
    for row in rows:
        xml_string = row[0]
        # Parse the XML string
        xml_element = etree.fromstring(xml_string)
        # Append the parsed XML element to the all_values element
        all_values.extend(xml_element)

    # Close the connection to the database
    conn.close()

    # Return the list of values from the specified column
    return all_values