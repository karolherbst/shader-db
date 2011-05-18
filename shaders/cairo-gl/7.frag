uniform vec4 source_constant;
vec4 get_source()
{
    return source_constant;
}
uniform sampler2D mask_sampler;
varying vec2 mask_texcoords;
vec4 get_mask()
{
    return texture2D(mask_sampler, mask_texcoords);
}
void main()
{
    gl_FragColor = get_source() * get_mask();
}

