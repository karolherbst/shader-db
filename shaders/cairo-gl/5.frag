uniform sampler2D source_sampler;
varying vec2 source_texcoords;
vec4 get_source()
{
    return texture2D(source_sampler, source_texcoords);
}
varying float mask_coverage;
vec4 get_mask()
{
    return vec4(0, 0, 0, mask_coverage);
}
void main()
{
    gl_FragColor = get_source() * get_mask().a;
}

