precision mediump float;
varying vec2 v_texcoord;
uniform sampler2D tex;
uniform float alpha;
uniform float texwidth;
void main()
{
   if (v_texcoord.x < 0.0 || v_texcoord.x > texwidth ||
       v_texcoord.y < 0.0 || v_texcoord.y > 1.0)
      discard;
   gl_FragColor = texture2D(tex, v_texcoord)
;   gl_FragColor = alpha * gl_FragColor;
}

