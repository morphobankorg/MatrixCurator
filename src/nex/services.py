from io import BytesIO
from .exceptions import log_execution, handle_exceptions


class NexService:
    def __init__(self, file: BytesIO):
        self.nexus_file = file.read().decode("utf-8")
        self.character_states = None

    @log_execution
    @handle_exceptions
    def _character_states(self, character_states_list: list[dict]) -> list[str]:
        """
        Builds CHARSTATELABELS from a list of character dictionaries, 
        formatted as specified, using 'character_index' for numbering.

        Args:
            characters_list: List of character dictionaries.

        Returns:
            list: List of formatted CHARSTATELABELS strings.
        """

        character_states = []

        for character_states_dict in character_states_list:
            # Extract data from dictionary
            character_index = character_states_dict['character_index']
            name = character_states_dict['character'].replace("'", "?")  # Escape single quotes
            states_list = character_states_dict['states']
            
            # Format states (without escaping internal quotes)
            states = ["'" + state + "'" for state in states_list]
            label = f"{character_index} '{name}' / {' '.join(states)},"
            character_states.append("\t\t" + label)

        # Replace trailing comma with semicolon on last line
        if character_states:
            last_label = character_states[-1]
            character_states[-1] = last_label[:-1] + ";"

        return character_states
    
    @log_execution
    @handle_exceptions
    def nexus_update(self) -> str:
        
        lines = self.nexus_file.splitlines()

        # Deletion Logic
        charstatelabels_start_index = None
        charstatelabels_end_index = None
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith("CHARSTATELABELS"):
                charstatelabels_start_index = i
            elif charstatelabels_start_index is not None and stripped_line.startswith(";"):
                charstatelabels_end_index = i
                break

        if charstatelabels_start_index is not None and charstatelabels_end_index is not None:
            del lines[charstatelabels_start_index:charstatelabels_end_index + 1]

        # Insertion Logic
        matrix_index = None
        matrix_indent = None
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith("MATRIX"):
                matrix_index = i
                matrix_indent = len(line) - len(line.lstrip())
                break

        if matrix_index is not None:
            insert_index = matrix_index
            indented_lines = [f"{' ' * matrix_indent}{label}\n" for label in self.character_states]
            lines[insert_index:insert_index] = [f"{' ' * matrix_indent}\tCHARSTATELABELS\n"] + indented_lines
            
        new_nexus_content = "\n".join(lines)
        return new_nexus_content
    
    def update(self, character_states_list: list[dict]) -> str:
        self.character_states = self._character_states(character_states_list=character_states_list)
        return self.nexus_update()