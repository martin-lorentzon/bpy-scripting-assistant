import bpy
from bpy.props import BoolProperty
import re
import time
import threading
import queue

from .text_helpers import get_cursor_index
from .autocomplete_shader import draw_autocomplete
from .ollama import get_completion


class BPYSA_OT_toggle_code_completion(bpy.types.Operator):
    bl_idname = "text.toggle_code_completion"
    bl_label = "Toggle Code Completion"
    bl_description = "Show suggestions while typing"

    _draw_handler = None

    def invoke(self, context, event):
        if context.window_manager.code_completion_running:
            context.window_manager.code_completion_running = False
            BPYSA_OT_toggle_code_completion._remove_draw_handler()
            return {"CANCELLED"}

        self.space_data = context.space_data
        context.window_manager.modal_handler_add(self)
        context.window_manager.code_completion_running = True

        BPYSA_OT_toggle_code_completion._draw_handler = bpy.types.SpaceTextEditor.draw_handler_add(
            draw_autocomplete, (self,), "WINDOW", "POST_PIXEL"
        )
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not context.window_manager.code_completion_running or not self.space_data.text:
            context.window_manager.code_completion_running = False

            BPYSA_OT_toggle_code_completion._remove_draw_handler()

            if context.area:
                context.area.tag_redraw()
            return {"CANCELLED"}

        addon_prefs = context.preferences.addons[__package__].preferences

        text_data: bpy.types.Text = self.space_data.text

        cursor_index = get_cursor_index(text_data)

        full_text = text_data.as_string()
        raw_prefix = full_text[:cursor_index]
        raw_suffix = full_text[cursor_index:]

        prefix_lines = raw_prefix.splitlines()
        suffix_lines = raw_suffix.splitlines()

        def remove_comments(lines: list[str]) -> list[str]:
            """Src: https://stackoverflow.com/a/73316105"""
            new_lines = []
            for line in lines:
                if line.startswith("#"):  # Deal with comment as the first character
                    continue

                line = line.split(" #")[0]
                if line.strip() != "":
                    new_lines.append(line)

            return new_lines

        prefix_lines = remove_comments(prefix_lines)
        suffix_lines = remove_comments(suffix_lines)

        prefix = "\n".join(prefix_lines[-2:])
        suffix = "\n".join(suffix_lines[:2])

        prompt = f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"

        if event.type == "TEXTINPUT":
            self.last_input_time = time.time()

        new_prompt = prompt != getattr(self, "last_prompt", "")
        debounce_ok = time.time() - getattr(self, "last_input_time", 0) > 0.5

        if new_prompt and debounce_ok:
            # self.text = prompt
            self.text = get_completion(addon_prefs.api_base_url, addon_prefs.api_model, prompt)

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
