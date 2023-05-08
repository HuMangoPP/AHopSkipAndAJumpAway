#version 330 core

layout (location = 0) in vec2 vertcoord;
layout (location = 1) in vec2 texcoord;

uniform mat4 m_model;

uniform vec2 res;
out vec2 uvs;
out vec2 screen_res;

void main() {
    uvs = texcoord;
    screen_res = res;
    gl_Position = m_model * vec4(vertcoord, 0.0, 1.0);
}