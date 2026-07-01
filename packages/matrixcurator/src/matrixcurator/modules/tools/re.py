from typing import Any, List, Dict
from langchain_core.tools import tool
from matrixcurator.exceptions import NexusFormatError

# Absolute import to avoid circular dependency with the file name
import re as python_re


@tool
def generate_with_re(
    original_nexus: str, extracted_states: List[Dict[str, Any]]
) -> bytes:
    """Use this tool to generate an updated NEXUS file by inserting the extracted character states."""
    if not original_nexus:
        raise NexusFormatError("Original NEXUS content is missing.")

    if "MATRIX" not in original_nexus.upper():
        raise NexusFormatError("MATRIX block not found in NEXUS file.")

    # Build CHARSTATELABELS block
    charstatelabels = "CHARSTATELABELS\n"
    for state in extracted_states:
        char_idx = state.get("character_index")
        char_name = state.get("character_name", "").replace("'", "''")
        states_dict = state.get("states", {})

        states_str = ""
        if states_dict:
            states_list = []
            for k, v in states_dict.items():
                v_clean = str(v).replace("'", "''")
                states_list.append(f"{k} '{v_clean}'")
            states_str = ", ".join(states_list)

        charstatelabels += f"\t{char_idx} '{char_name}' / {states_str},\n"

    # Remove trailing comma and add semicolon
    if charstatelabels.endswith(",\n"):
        charstatelabels = charstatelabels[:-2] + "\n;\n"
    else:
        charstatelabels += ";\n"

    # Insert before MATRIX
    # Find MATRIX case-insensitively
    matrix_match = python_re.search(r"\bMATRIX\b", original_nexus, python_re.IGNORECASE)
    if not matrix_match:
        raise NexusFormatError("MATRIX block not found in NEXUS file.")

    insert_pos = matrix_match.start()

    updated_nexus = (
        original_nexus[:insert_pos]
        + charstatelabels
        + "\n"
        + original_nexus[insert_pos:]
    )

    return updated_nexus.encode("utf-8")
