import bpy
from bpy.props import BoolProperty

import time
from . import session_manager
from .text_helpers import get_cursor_index
from .autocomplete_shader import draw_autocomplete
from .ollama import build_fim_prompt, get_completion


class BPYSA_OT_toggle_code_completion(bpy.types.Operator):
    bl_idname = "text.toggle_code_completion"
    bl_label = "Toggle Code Completion"
    bl_description = "Show suggestions while typing"

    _draw_handler = None

    @classmethod
    def poll(self, context):
        return session_manager.has_session()

    def invoke(self, context, event):
        if context.window_manager.code_completion_running:
            context.window_manager.code_completion_running = False
            BPYSA_OT_toggle_code_completion._remove_draw_handler()
            return {"CANCELLED"}

        self.space_data = context.space_data
        self.text = ""
        self.last_input_time = time.time()
        self.last_prompt = ""

        context.window_manager.modal_handler_add(self)
        context.window_manager.code_completion_running = True

        BPYSA_OT_toggle_code_completion._draw_handler = bpy.types.SpaceTextEditor.draw_handler_add(
            draw_autocomplete, (self,), "WINDOW", "POST_PIXEL"
        )
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not (context.window_manager.code_completion_running and self.space_data.text and session_manager.has_session()):
            context.window_manager.code_completion_running = False
            BPYSA_OT_toggle_code_completion._remove_draw_handler()

            if context.area:
                context.area.tag_redraw()
            return {"CANCELLED"}

        addon_prefs = context.preferences.addons[__package__].preferences

        # region Prompt Building
        text_data: bpy.types.Text = self.space_data.text

        cursor_index = get_cursor_index(text_data)

        full_text = text_data.as_string()
        raw_prefix = full_text[:cursor_index]
        raw_suffix = full_text[cursor_index:]

        prefix_lines = raw_prefix.splitlines()
        suffix_lines = raw_suffix.splitlines()

        prefix = "\n".join(prefix_lines[-40:])
        suffix = "\n".join(suffix_lines[:10])

        prompt = build_fim_prompt(prefix, suffix)
        # endregion

        if event.type == "TEXTINPUT":
            self.last_input_time = time.time()
            print("HELLO")
        debounce_ok = time.time() - self.last_input_time > 0.5

        new_prompt = prompt != self.last_prompt

        if new_prompt and debounce_ok:
            # self.text = prompt
            self.text = get_completion(
                session_manager.get_session(),
                addon_prefs.api_base_url,
                addon_prefs.api_model,
                prompt
            )

        self.last_prompt = prompt

        # Redraw to update overlay
        if context.area:
            context.area.tag_redraw()
        return {"PASS_THROUGH"}

    @classmethod
    def _remove_draw_handler(cls):
        if cls._draw_handler is not None:
            bpy.types.SpaceTextEditor.draw_handler_remove(cls._draw_handler, "WINDOW")
            cls._draw_handler = None


# ——————————————————————————————————————————————————————————————————————
# MARK: REGISTRATION
# ——————————————————————————————————————————————————————————————————————


basic_register, basic_unregister = bpy.utils.register_classes_factory(
    (
        BPYSA_OT_toggle_code_completion,
    ))


def register():
    basic_register()
    bpy.types.WindowManager.code_completion_running = BoolProperty(default=False)


def unregister():
    basic_unregister()
    del bpy.types.WindowManager.code_completion_running
