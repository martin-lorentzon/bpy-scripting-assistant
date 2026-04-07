import bpy
from bpy.types import AddonPreferences
from bpy.props import EnumProperty, StringProperty, IntProperty, FloatProperty, FloatVectorProperty
from threading import Thread
from .providers import PROVIDERS
from .models import MODELS
from . import session_manager


class BPYSAPreferences(AddonPreferences):
    bl_idname = __package__

    def get_provider(self):
        return next(p for p in PROVIDERS if p.code_id == self.llm_provider)

    def get_model_family(self, model_preference: str):
        for model in MODELS:
            activation_words = model.activation_words.split()
            if all(word in getattr(self, model_preference) for word in activation_words):
                return model
        return MODELS[0]

    # region: Model search
    _cached_models = []

    def fetch_models_async(self):
        def worker():
            BPYSAPreferences._cached_models = self.get_provider().get_models()

        Thread(target=worker, daemon=True).start()

    def model_search(self, context, edit_text):
        self.fetch_models_async()  # New results don't show until UI refresh (won't fix)
        return BPYSAPreferences._cached_models

    def llm_provider_update(self, context):
        self.base_url = self.get_provider().base_url
        self.fetch_models_async()
    # endregion

    provider_items = [(p.code_id, p.name, "") for p in PROVIDERS]

    llm_provider: EnumProperty(
        name="LLM Provider",
        description=(
            "The LLM provider used to serve the model."
        ),
        items=provider_items,
        update=llm_provider_update
    )
    base_url: StringProperty(
        name="API Base URL",
        default=PROVIDERS[0].base_url
    )
    code_completion_model: StringProperty(
        name="Code Completion Model",
        default="qwen2.5-coder:1.5b-base-q4_K_M",
        search=model_search,
    )
    fim_prefix_lines: IntProperty(
        name="Prefix Lines",
        description="The number of lines *before* the cursor to use as context",
        default=40,
        min=1,
        max=100
    )
    fim_suffix_lines: IntProperty(
        name="Suffix Lines",
        description="The number of lines *after* the cursor to use as context",
        default=10,
        min=1,
        max=100
    )
    debounce_time: FloatProperty(
        name="Suggestion Delay",
        description="Delay after typing before code completion activates",
        min=0.1,
        max=5.0,
        default=0.5,
        subtype="TIME_ABSOLUTE"
    )
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
        default=1.0
    )
    autocomplete_border_feather: FloatProperty(
        name="Autocomplete Border Feather",
        default=1.0
    )
    autocomplete_horizontal_offset: FloatProperty(
        name="Autocomplete Horizontal Offset",
        default=0.0
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        header, panel = layout.panel("bpysa_api_panel")
        header.label(text="API Settings")

        if panel:
            panel.prop(self, "llm_provider")
            panel.prop(self, "base_url")
            panel.separator()
            panel.prop(self, "model")
            panel.separator()
            row = panel.row()
            row.operator("bpysa.create_session", text="Connect")
            sub = row.row()
            sub.enabled = session_manager.has_session()
            sub.operator("bpysa.close_session", text="Disconnect")

        header, panel = layout.panel("bpysa_autocomplete_panel", default_closed=True)
        header.label(text="Code Completion")

        if panel:
            panel.prop(self, "debounce_time")
            panel.prop(self, "fim_prefix_lines")
            panel.prop(self, "fim_suffix_lines")

        header, panel = layout.panel("bpysa_theme_panel", default_closed=True)
        header.label(text="Theme")

        if panel:
            box = panel.box()
            box.label(text="Autocomplete Overlay")

            box.prop(self, "autocomplete_bg_color", text="Background Color")
            box.prop(self, "autocomplete_text_color", text="Text Color")
            box.prop(self, "autocomplete_padding", text="Padding")
            box.prop(self, "autocomplete_corner_radius", text="Corner Radius")
            box.prop(self, "autocomplete_border_feather", text="Border Feather")
            box.prop(self, "autocomplete_horizontal_offset", text="Horizontal Offset")


# ——————————————————————————————————————————————————————————————————————
# MARK: REGISTRATION
# ——————————————————————————————————————————————————————————————————————


basic_register, unregister = bpy.utils.register_classes_factory((BPYSAPreferences,))


def register():
    basic_register()
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    addon_prefs.fetch_models_async()
