#define FRAGMENT_SHADER
// Warsow GLSL shader

#if !defined(__GLSL_CG_DATA_TYPES)
#define myhalf float
#define myhalf2 vec2
#define myhalf3 vec3
#define myhalf4 vec4
#else
#define myhalf half
#define myhalf2 half2
#define myhalf3 half3
#define myhalf4 half4
#endif

#define M_TWOPI 6.28318530717958647692

varying vec2 TexCoord;

#ifdef VERTEX_SHADER
// Vertex shader

uniform float TurbAmplitude, TurbPhase;

void main(void)
{
gl_FrontColor = gl_Color;

vec4 turb;
turb = vec4(gl_MultiTexCoord0);
turb.s += TurbAmplitude * sin( ((gl_MultiTexCoord0.t / 4.0 + TurbPhase)) * M_TWOPI );
turb.t += TurbAmplitude * sin( ((gl_MultiTexCoord0.s / 4.0 + TurbPhase)) * M_TWOPI );
TexCoord = vec2(gl_TextureMatrix[0] * turb);

gl_Position = ftransform();
#ifdef APPLY_CLIPPING
#ifdef __GLSL_CG_DATA_TYPES
gl_ClipVertex = gl_ModelViewMatrix * gl_Vertex;
#endif
#endif
}

#endif // VERTEX_SHADER


#ifdef FRAGMENT_SHADER
// Fragment shader

uniform sampler2D BaseTexture;

void main(void)
{

myhalf4 color;

color = myhalf4(gl_Color) * myhalf4(texture2D(BaseTexture, TexCoord));

gl_FragColor = vec4(color);
}

#endif // FRAGMENT_SHADER


