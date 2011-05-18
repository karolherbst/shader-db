varying vec2 mask_texcoords;
attribute vec4 Vertex;
attribute vec4 Color;
attribute vec4 MultiTexCoord0;
attribute vec4 MultiTexCoord1;
uniform mat4 ModelViewProjectionMatrix;
void main()
{
    gl_Position = ModelViewProjectionMatrix * Vertex;
    mask_texcoords = MultiTexCoord1.xy;
}

