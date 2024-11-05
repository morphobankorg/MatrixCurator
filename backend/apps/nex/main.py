def insert_or_replace_charstatelabels(nexus_file, charstatelabels):

    nexus_content = nexus_file.read().decode('utf-8') 
    lines = nexus_content.splitlines()  # Split into lines

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

    #  Insertion Logic
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
        indented_lines = [f"{' ' * matrix_indent}{label}\n" for label in charstatelabels]
        lines[insert_index:insert_index] = [f"{' ' * matrix_indent}\tCHARSTATELABELS\n"] + indented_lines

        
    new_nexus_content = "\n".join(lines)  # Combine lines using newlines
    return new_nexus_content