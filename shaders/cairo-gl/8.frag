uniform vec4 source_constant;
vec4 get_source()
{
    return source_constant;
}
vec4 get_mask()
{
    return vec4 (0, 0, 0, 1);
}
void main()
{
    gl_FragColor = get_source() * get_mask().a;
}

