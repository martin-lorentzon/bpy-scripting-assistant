import bpy
import inspect
import textwrap


# ——————————————————————————————————————————————————————————————————————
# MARK: INTERFACE
# ——————————————————————————————————————————————————————————————————————


draw_injection = """
if text:
    layout.separator_spacer()
    row = layout.row()
    row.active = is_syntax_highlight_supported
    modal_is_running = context.window_manager.code_completion_running
    row.operator(
        "text.toggle_code_completion",
        text="",
        icon="OUTLINER_OB_LIGHT" if modal_is_running else "LIGHT",
        depress=modal_is_running,
    )
"""


def new_header_draw_factory(original_draw):
    source = inspect.getsource(original_draw)
    source = textwrap.dedent(source)
    insert_after = 'row.operator("text.run_script", text="", icon=\'PLAY\')'

    def indent_multiline(text: str, spaces: int | str) -> str:
        prefix = " " * spaces
        return "\n".join(prefix + line for line in text.splitlines())

    source = source.replace(
        insert_after,
        insert_after + "\n" + indent_multiline(draw_injection, 4)
    )

    globs = {**original_draw.__globals__, "draw_injection": draw_injection}
    namespace = {}
    exec(source, globs, namespace)
    return namespace["draw"]


# ——————————————————————————————————————————————————————————————————————
# MARK: REGISTRATION
# ——————————————————————————————————————————————————————————————————————


# basic_register, basic_unregister = bpy.utils.register_classes_factory(
#     (
#         BPYSA_PT_...,
#     ))

_original_header_draw = None


def register():
    # basic_register()

    global _original_header_draw
    _original_header_draw = bpy.types.TEXT_HT_header.draw
    bpy.types.TEXT_HT_header.draw = new_header_draw_factory(_original_header_draw)


def unregister():
    # basic_unregister()

    global _original_header_draw
    bpy.types.TEXT_HT_header.draw = _original_header_draw
