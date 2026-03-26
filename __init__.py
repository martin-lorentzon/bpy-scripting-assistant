bl_info = {
    "name": "BPY Scripting Assistant",
    "description": "bpy, but you remember the syntax",
    "author": "Martin Lorentzon <mtlorentzon@proton.me>",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Text Editor > Header",
    "doc_url": "https://github.com/martin-lorentzon/bpy-scripting-assistant",
    "tracker_url": "https://github.com/martin-lorentzon/bpy-scripting-assistant/issues",
    "warning": "Experimental",
    "support": "COMMUNITY",
    "category": "Development",
}


# ——————————————————————————————————————————————————————————————————————
# MARK: IMPORTS
# ——————————————————————————————————————————————————————————————————————


# fmt: off
_needs_reload = "bpy" in locals()

import bpy
from . import addon_preferences
from . import ollama
from . import autocomplete_shader
from . import modal_operator
from . import ui


if _needs_reload:
    from importlib import reload

    reload(addon_preferences)
    reload(ollama)
    reload(autocomplete_shader)
    reload(modal_operator)
    reload(ui)
# fmt: on


# ——————————————————————————————————————————————————————————————————————
# MARK: REGISTRATION
# ——————————————————————————————————————————————————————————————————————


modules = [
    addon_preferences,
    modal_operator,
    ui,
]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()
