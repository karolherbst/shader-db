#define VERTEX_SHADER
// Warsow GLSL shader


varying vec4 ProjVector;

#ifdef VERTEX_SHADER
// Vertex shader

uniform float OutlineHeight;

void main(void)
{
gl_FrontColor = gl_Color;

vec4 n = vec4(gl_Normal.xyz, 0.0);
vec4 v = vec4(gl_Vertex) + n * OutlineHeight;

gl_Position = gl_ModelViewProjectionMatrix * v;
ProjVector = gl_Position;
#ifdef APPLY_CLIPPING
#ifdef __GLSL_CG_DATA_TYPES
gl_ClipVertex = gl_ModelViewMatrix * v;
#endif
#endif
}

#endif // VERTEX_SHADER


#ifdef FRAGMENT_SHADER
// Fragment shader

uniform float OutlineCutOff;

void main(void)
{

#ifdef APPLY_OUTLINES_CUTOFF
if (OutlineCutOff > 0.0 && (ProjVector.w > OutlineCutOff))
discard;
#endif

gl_FragColor = vec4 (gl_Color);
}

#endif // FRAGMENT_SHADER


