import bpy
import gpu
import blf
from gpu_extras.batch import batch_for_shader


SCROLLBAR_W = 17


# Create Shader Info
io = gpu.types.GPUStageInterfaceInfo("io")
io.smooth('VEC2', "v_uv")

shader_info = gpu.types.GPUShaderCreateInfo()
shader_info.push_constant('VEC2', "offset")
shader_info.push_constant('VEC2', "size")
shader_info.push_constant('VEC2', "canvas_size")
shader_info.push_constant('FLOAT', "radius")
shader_info.push_constant('VEC4', "color")
shader_info.push_constant('FLOAT', "feather")
shader_info.vertex_in(0, 'VEC2', "pos")
shader_info.vertex_out(io)
shader_info.fragment_out(0, 'VEC4', "fragColor")

coords = [(0, 0), (1, 0), (0, 1), (1, 1)]  # Unit Quad

shader_info.vertex_source("""
    void main() {
        v_uv = pos;
        // Scale and position the unit quad to given pixel dimensions on the UI canvas
        vec2 pixel_pos = offset + (pos * size);
        vec2 ndc = (pixel_pos / canvas_size) * 2.0 - 1.0;
        gl_Position = vec4(ndc, 0.0, 1.0);
    }
""")

shader_info.fragment_source("""
    void main() {
        vec2 pixel_coord = v_uv * size;
        vec2 q = abs(pixel_coord - size * 0.5) - size * 0.5 + radius;
        float dist = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;

        // -dist = distance from nearest edge, inward (0 at edge, positive inside)
        float alpha = smoothstep(0.0, feather, -dist);

        fragColor = vec4(color.rgb, color.a * alpha);
    }
""")

shader = gpu.shader.create_from_info(shader_info)
batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": coords})


def draw_autocomplete(op):
    if op._text == "":
        return

    context = bpy.context
    region = context.region
    st = context.space_data

    if not (st.type == 'TEXT_EDITOR' and st.text and st.is_syntax_highlight_supported()):
        return

    prefs = context.preferences
    addon_prefs = context.preferences.addons[__package__].preferences

    # Font Setup & Measurement
    scale = prefs.system.ui_scale * 1  # prefs.system.pixel_size also exists, not sure if and how to use it
    font_id = 1
    font_size = st.font_size * scale
    blf.size(font_id, font_size)
    character_w, character_h = blf.dimensions(font_id, "|")

    text_w, text_h = blf.dimensions(font_id, op._text)
    padding = addon_prefs.autocomplete_padding * font_size
    background_w, background_h = text_w + (padding * 2), character_h + (padding * 2)

    # Get cursor position
    cursor_x, cursor_y = st.region_location_from_cursor(
        st.text.current_line_index,
        st.text.current_character
    )
    offset_x = character_w * addon_prefs.autocomplete_horizontal_offset
    offset_y = character_h / 4
    base_x = cursor_x + offset_x - padding
    base_y = cursor_y + offset_y / 2 - padding

    # Clip to exclude scrollbar
    scrollbar_w = round(SCROLLBAR_W * scale)
    clip_w = region.width - scrollbar_w

    gpu.state.scissor_test_set(True)
    gpu.state.scissor_set(0, 0, clip_w, region.height)

    # Draw background
    gpu.state.blend_set('ALPHA')
    shader.bind()
    shader.uniform_float("offset", (base_x, base_y))
    shader.uniform_float("size", (background_w, background_h))
    shader.uniform_float("canvas_size", (region.width, region.height))
    shader.uniform_float("color", addon_prefs.autocomplete_bg_color)
    shader.uniform_float("radius", addon_prefs.autocomplete_corner_radius * font_size)
    shader.uniform_float("feather", addon_prefs.autocomplete_border_feather * font_size)
    batch.draw(shader)

    # Draw text
    blf.position(font_id, cursor_x + offset_x, cursor_y + offset_y, 0)
    blf.color(font_id, *addon_prefs.autocomplete_text_color)
    blf.draw(font_id, op._text)

    gpu.state.blend_set('NONE')
    gpu.state.scissor_test_set(False)
