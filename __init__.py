bl_info = {
    "name": "BPY Scripting Assistant",
    "description": "Code suggestions for Blender Python using an LLM",
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
from . import providers
from . import session_manager
from . import addon_preferences
from . import session_operators
from . import autocomplete_shader
from . import modal_operator
from . import ui


if _needs_reload:
    from importlib import reload

    reload(providers)
    reload(session_manager)
    reload(addon_preferences)
    reload(session_operators)
    reload(autocomplete_shader)
    reload(modal_operator)
    reload(ui)
# fmt: on


# ——————————————————————————————————————————————————————————————————————
# MARK: REGISTRATION
# ——————————————————————————————————————————————————————————————————————


modules = [
    addon_preferences,
    session_operators,
    modal_operator,
    ui,
]


def register():
    for module in modules:
        module.register()


def unregister():
    session_manager.close_session()

    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()
