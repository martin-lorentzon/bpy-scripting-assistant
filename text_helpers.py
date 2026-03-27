import bpy


def get_cursor_index(text_data: bpy.types.Text):
    lines = text_data.lines
    line_index = text_data.current_line_index
    char_index = text_data.current_character
    return sum(len(lines[i].body) + 1 for i in range(line_index)) + char_index
