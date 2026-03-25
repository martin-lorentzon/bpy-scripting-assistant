import bpy
from bpy.types import AddonPreferences
from bpy.props import FloatProperty, FloatVectorProperty


class BPYSAPreferences(AddonPreferences):
    bl_idname = __package__

    autocomplete_bg_color: FloatVectorProperty(
        name="Autocomplete Background Color",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.1, 0.1, 0.1, 0.9)
    )
    autocomplete_text_color: FloatVectorProperty(
        name="Autocomplete Text Color",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.7, 0.7, 0.7, 1.0)
    )
    autocomplete_padding: FloatProperty(
        name="Autocomplete Padding",
        default=0.5
    )
    autocomplete_corner_radius: FloatProperty(
        name="Autocomplete Corner Radius",
        default=0.5
    )
    autocomplete_border_feather: FloatProperty(
        name="Autocomplete Border Feather",
        default=0.25
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        header, panel = layout.panel("bpysa_theme_panel")
        header.label(text="Theme")

        if panel:
            box = panel.box()
            box.label(text="Autocomplete")

            box.prop(self, "autocomplete_bg_color", text="Background Color")
            box.prop(self, "autocomplete_text_color", text="Text Color")
            box.prop(self, "autocomplete_padding", text="Padding")
            box.prop(self, "autocomplete_corner_radius", text="Corner Radius")
            box.prop(self, "autocomplete_border_feather", text="Border Feather")


# ——————————————————————————————————————————————————————————————————————
# MARK: REGISTRATION
# ——————————————————————————————————————————————————————————————————————


register, unregister = bpy.utils.register_classes_factory((BPYSAPreferences,))
