#ifdef GL_ES
precision mediump float;
#endif
uniform sampler2D source_sampler;
uniform vec2 source_texdims;
varying vec2 source_texcoords;
vec4 get_source()
{
    return texture2D (source_sampler, source_texcoords);
}
vec4 get_mask()
{
    return vec4 (0, 0, 0, 1);
}
void main()
{
    gl_FragColor = get_source() * get_mask().a;
}

