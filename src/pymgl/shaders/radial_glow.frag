#version 330 core

layout (location = 0) out vec4 fragColor;

in vec2 uvs;
in vec2 screen_res;

uniform sampler2D tex;

void main() {
    vec2 st = gl_FragCoord.xy/screen_res;
    vec3 color = vec3(st.x, 0.0, st.y) * vec3(texture(tex, uvs));
    float alpha = 1.0;
    if ((color.r + color.g + color.b) == 0) {
        alpha = (0.5 - distance(uvs, vec2(0.5)));
        color = vec3(0.75, 0.75, 1.0);
    } else {
        alpha = 1.0;
    }
    // color += 0.01 / length(uvs - vec2(0.5));
    fragColor = vec4(color, 1.0);
}