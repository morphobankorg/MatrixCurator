import re
from typing import Any, List, Dict
from matrixcurator.exceptions import NexusFormatError


def read_nexus(file_content: bytes, **kwargs) -> str:
    try:
        return file_content.decode("utf-8")
    except Exception as e:
        raise NexusFormatError(f"Failed to read NEXUS file: {str(e)}") from e


def write_nexus(
    original_nexus: str, extracted_states: List[Dict[str, Any]], **kwargs
) -> bytes:
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
    matrix_match = re.search(r"\bMATRIX\b", original_nexus, re.IGNORECASE)
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
