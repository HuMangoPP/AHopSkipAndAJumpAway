#version 330 core

#define TAU 6.2831855

layout (location = 0) out vec4 fragColor;

in vec2 uvs;
in vec2 screen_res;

uniform sampler2D tex;

float plot(vec2 st, float pct){
  return  smoothstep( pct-0.01, pct, st.y) -
          smoothstep( pct, pct+0.01, st.y);
}

void main() {
    vec2 st = gl_FragCoord.xy/screen_res;
    float dist_from_center = distance(gl_FragCoord.xy, 0.5 * vec2(screen_res.x, screen_res.y*5.0/4.0));

    vec3 color = vec3(texture(tex, uvs));
    if ((color.r + color.g + color.b == 3.0)) {
        if (dist_from_center > 0.3 * screen_res.y || st.y < 0.5) {
            // background gradient
            color = vec3(1.1-st.y, st.y - 0.4, 0.9) * color;
            // glowing line separator
            // float pct = plot(st,sin(20.0 * TAU * st.x)*0.05+0.5);
            // color = (1.0-pct)*color+pct*vec3(1.0,0.75,1.0);
            // pct = plot(st,cos(20.0 * TAU * st.x)*0.05+0.5);
            // color = (1.0-pct)*color+pct*vec3(1.0,0.75,1.0);
        } else {
            // gradient sun
            if (st.y < 2.5/4.0 && sin(25.0 * TAU * (2.5/4.0-st.y)) > 0) {
                color = vec3(1.1-st.y, st.y - 0.4, 0.9) * color;
            } else {
                color = vec3(1.0, st.y-0.2, st.y-0.5) * color;
            }
        }
    }

    fragColor = vec4(color, 1.0);
}