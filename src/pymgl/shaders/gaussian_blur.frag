#version 330 core
#define KERNEL_SIZE 8

layout (location = 0) out vec4 fragColor;

in vec2 uvs;
in vec2 screen_res;

uniform sampler2D tex;
uniform float weight[KERNEL_SIZE] = float[] (0.1974,	0.1747,	0.1210,	0.0656,	0.0278,	0.0092,	0.0024,	0.0005);

void main() {
    vec2 st = gl_FragCoord.xy/screen_res;

    vec2 tex_offset = 5.0 / textureSize(tex, 0);
    vec4 color = vec4(texture(tex, uvs).rgba);
    // horizontal
    for (int i = 1; i < KERNEL_SIZE; i++) {
        color += vec4(texture(tex, uvs + vec2(tex_offset.x * i, 0.0)).rgba) * weight[i];
        color += vec4(texture(tex, uvs - vec2(tex_offset.x * i, 0.0)).rgba) * weight[i];
    }
    // vertical
    for (int i = 1; i < KERNEL_SIZE; i++) {
        color += vec4(texture(tex, uvs + vec2(0.0, tex_offset.y * i)).rgba) * weight[i];
        color += vec4(texture(tex, uvs - vec2(0.0, tex_offset.y * i)).rgba) * weight[i];
    }

    fragColor = vec4(color.rgb, color.r + color.g + color.b);
}