import bpy
from . import session_manager


def redraw_text_editors():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "TEXT_EDITOR":
                area.tag_redraw()


class BPYSA_OT_create_session(bpy.types.Operator):
    bl_idname = "bpysa.create_session"
    bl_label = "Connect to API"
    bl_description = "Create a session and verify connection to the API"

    def execute(self, context):
        addon_prefs = context.preferences.addons[__package__].preferences

        ok, msg = session_manager.create_and_test(addon_prefs.base_url)

        if not ok:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        self.report({"INFO"}, msg)

        redraw_text_editors()
        return {'FINISHED'}


class BPYSA_OT_close_session(bpy.types.Operator):
    bl_idname = "bpysa.close_session"
    bl_label = "Disconnect Session"
    bl_description = "Close the current connection to the API"

    def execute(self, context):
        session_manager.close_session()

        self.report({"INFO"}, "Disconnected from API")

        redraw_text_editors()
        return {"FINISHED"}


# ——————————————————————————————————————————————————————————————————————
# MARK: REGISTRATION
# ——————————————————————————————————————————————————————————————————————


basic_register, basic_unregister = bpy.utils.register_classes_factory(
    (
        BPYSA_OT_create_session,
        BPYSA_OT_close_session,
    ))


def register():
    basic_register()


def unregister():
    basic_unregister()
