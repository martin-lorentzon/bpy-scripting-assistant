import bpy
from bpy.props import BoolProperty
from .autocomplete_shader import draw_autocomplete

# ——————————————————————————————————————————————————————————————————————
# MARK: OPERATOR
# ——————————————————————————————————————————————————————————————————————


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

        # Register draw handler
        BPYSA_OT_toggle_code_completion._draw_handler = bpy.types.SpaceTextEditor.draw_handler_add(
            draw_autocomplete, (), "WINDOW", "POST_PIXEL"
        )

        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not context.window_manager.code_completion_running or not self.space_data.text:
            context.window_manager.code_completion_running = False
            BPYSA_OT_toggle_code_completion._remove_draw_handler()
            if context.area:
                context.area.tag_redraw()
            return {"CANCELLED"}

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
