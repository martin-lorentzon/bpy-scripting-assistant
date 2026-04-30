import bpy
from bpy.props import BoolProperty
import threading
import time
from .addon_preferences import BPYSAPreferences
from . import session_manager
from .text_helpers import get_cursor_index
from .providers import BaseLLMProvider
from .models import BaseModelFamily
from .autocomplete_shader import draw_autocomplete


class BPYSA_OT_toggle_code_completion(bpy.types.Operator):
    bl_idname = "text.toggle_code_completion"
    bl_label = "Toggle Code Completion"
    bl_description = "Show suggestions while typing"

    _draw_handler = None

    @classmethod
    def poll(cls, context):
        return session_manager.has_session()

    def invoke(self, context, event):
        if context.window_manager.code_completion_running:
            context.window_manager.code_completion_running = False
            BPYSA_OT_toggle_code_completion._remove_draw_handler()
            return {"CANCELLED"}

        self._area_to_redraw = context.area

        self._last_prompt = ""
        self._request_id = 0
        
        self._text_to_insert = ""

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
            self._area_to_redraw.tag_redraw()
            return {"CANCELLED"}

        addon_prefs: BPYSAPreferences = context.preferences.addons[__package__].preferences
        model_family: BaseModelFamily = addon_prefs.get_model_family("code_completion_model")

        # region Prompt Building
        text_data: bpy.types.Text = context.space_data.text
        cursor_index = get_cursor_index(text_data)
        full_text = text_data.as_string()

        raw_prefix = full_text[:cursor_index]
        raw_suffix = full_text[cursor_index:]

        prefix_lines = raw_prefix.splitlines()[-addon_prefs.fim_prefix_lines:]
        suffix_lines = raw_suffix.splitlines()[:addon_prefs.fim_suffix_lines]

        prefix = "\n".join(prefix_lines)
        suffix = "\n".join(suffix_lines)

        prompt = model_family.build_fim_prompt(prefix, suffix, system_prompt=addon_prefs.code_completion_system_prompt)
        # endregion

        #if event.unicode != "" or event.type in {'BACK_SPACE', 'DEL', 'RET'}:
            #self._last_input_time = time.time()

        #debounce_ok = (time.time() - self._last_input_time) > addon_prefs.debounce_time
        new_prompt = prompt != self._last_prompt

        if new_prompt:
            def worker(self):
                current_request = self._request_id
                provider: BaseLLMProvider = addon_prefs.get_provider()

                result = provider.prompt(
                    session_manager.get_session(),
                    addon_prefs.base_url,
                    addon_prefs.code_completion_model,
                    prompt,
                    stop = model_family.fim_stop_tokens + ["\n"]  # TODO: Add support for multiline completions
                )

                if current_request == self._request_id:
                    self._text_to_insert = result
                    bpy.app.timers.register(self._area_to_redraw.tag_redraw, first_interval=0.0)

            self._request_id += 1
            self._thread = threading.Thread(target=worker, args=(self,), daemon=True).start()

        self._last_prompt = prompt

        if event.type == "TAB" and event.value == "PRESS":
            bpy.ops.text.insert(text=self._text_to_insert)
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
