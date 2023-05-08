#version 330 core

layout (location = 0) out vec4 fragColor;

in vec2 uvs;
in vec2 screen_res;

uniform sampler2D tex;

void main() {
    vec2 st = gl_FragCoord.xy/screen_res;
    vec3 color = vec3(st.x, 0.0, st.y) * vec3(texture(tex, uvs));
    float alpha = (1-step(0.5, distance(uvs, vec2(0.5))));
    color = alpha * color;
    fragColor = vec4(color, alpha);
}