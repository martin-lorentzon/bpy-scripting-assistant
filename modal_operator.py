import bpy
from bpy.props import BoolProperty
import threading
import time

from . import session_manager
from .text_helpers import get_cursor_index
from .autocomplete_shader import draw_autocomplete
from .ollama import get_completion
from .qwen_coder import build_fim_prompt


class BPYSA_OT_toggle_code_completion(bpy.types.Operator):
    bl_idname = "text.toggle_code_completion"
    bl_label = "Toggle Code Completion"
    bl_description = "Show suggestions while typing"

    _draw_handler = None

    def _run_completion(self, area, addon_prefs, prompt, current_request):
        result = get_completion(
            session_manager.get_session(),
            addon_prefs.base_url,
            addon_prefs.model,
            prompt
        )
        if current_request == self._request_id:
            self._text = result

            def redraw():
                if area:
                    area.tag_redraw()
                return None

            bpy.app.timers.register(redraw, first_interval=0.0)

    @classmethod
    def poll(cls, context):
        return session_manager.has_session()

    def invoke(self, context, event):
        if context.window_manager.code_completion_running:
            context.window_manager.code_completion_running = False
            BPYSA_OT_toggle_code_completion._remove_draw_handler()
            return {"CANCELLED"}

        self._text = ""
        self._last_input_time = time.time()
        self._last_prompt = ""

        self._thread = None
        self._request_id = 0

        context.window_manager.modal_handler_add(self)
        context.window_manager.code_completion_running = True

        BPYSA_OT_toggle_code_completion._draw_handler = bpy.types.SpaceTextEditor.draw_handler_add(
            draw_autocomplete, (self,), "WINDOW", "POST_PIXEL"
        )
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not (context.window_manager.code_completion_running and context.space_data.text and session_manager.has_session()):
            context.window_manager.code_completion_running = False
            BPYSA_OT_toggle_code_completion._remove_draw_handler()
            if context.area:
                context.area.tag_redraw()
            return {"CANCELLED"}

        addon_prefs = context.preferences.addons[__package__].preferences

        # region Prompt Building
        text_data: bpy.types.Text = context.space_data.text
        cursor_index = get_cursor_index(text_data)
        full_text = text_data.as_string()

        raw_prefix = full_text[:cursor_index]
        raw_suffix = full_text[cursor_index:]

        prefix_lines = raw_prefix.splitlines()
        suffix_lines = raw_suffix.splitlines()

        prefix = "\n".join(prefix_lines[-addon_prefs.fim_prefix_lines:])
        suffix = "\n".join(suffix_lines[:addon_prefs.fim_suffix_lines])

        print(addon_prefs.model_family)

        prompt = build_fim_prompt(prefix, suffix)
        # endregion

        if event.unicode != "" or event.type in {'BACK_SPACE', 'DEL', 'RET'}:
            self._last_input_time = time.time()

        debounce_ok = (time.time() - self._last_input_time) > addon_prefs.debounce_time
        new_prompt = prompt != self._last_prompt

        if new_prompt:
            self._request_id += 1
            self._thread = threading.Thread(
                target=self._run_completion,
                args=(context.area, addon_prefs, prompt, self._request_id),
                daemon=True
            )
            self._thread.start()

        self._last_prompt = prompt

        if event.type == "TAB" and event.value == "PRESS":
            bpy.ops.text.insert(text=self._text)
            return {"RUNNING_MODAL"}

        context.area.tag_redraw()
        return {"PASS_THROUGH"}

    @classmethod
    def _remove_draw_handler(cls):
        if cls._draw_handler is not None:
            try:
                bpy.types.SpaceTextEditor.draw_handler_remove(cls._draw_handler, "WINDOW")
            except Exception:
                pass
            cls._draw_handler = None


# ——————————————————————————————————————————————————————————————————————
# MARK: REGISTRATION
# ——————————————————————————————————————————————————————————————————————

basic_register, basic_unregister = bpy.utils.register_classes_factory(
    (BPYSA_OT_toggle_code_completion,)
)


def register():
    basic_register()
    bpy.types.WindowManager.code_completion_running = BoolProperty(default=False)


def unregister():
    basic_unregister()
    del bpy.types.WindowManager.code_completion_running
