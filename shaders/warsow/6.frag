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

varying vec4 TexCoord;
varying vec4 ProjVector;
#ifdef APPLY_EYEDOT
varying vec3 EyeVector;
#endif

#ifdef VERTEX_SHADER
// Vertex shader

#ifdef APPLY_EYEDOT
uniform vec3 EyeOrigin;
uniform float FrontPlane;
#endif

void main(void)
{
gl_FrontColor = gl_Color;

mat4 textureMatrix;

textureMatrix = gl_TextureMatrix[0];
TexCoord.st = vec2 (textureMatrix * gl_MultiTexCoord0);

textureMatrix = gl_TextureMatrix[0];
textureMatrix[0] = -textureMatrix[0];
textureMatrix[1] = -textureMatrix[1];
TexCoord.pq = vec2 (textureMatrix * gl_MultiTexCoord0);

#ifdef APPLY_EYEDOT
mat3 strMatrix;
strMatrix[0] = gl_MultiTexCoord1.xyz;
strMatrix[2] = gl_Normal.xyz;
strMatrix[1] = gl_MultiTexCoord1.w * cross (strMatrix[2], strMatrix[0]);

vec3 EyeVectorWorld = (EyeOrigin - gl_Vertex.xyz) * FrontPlane;
EyeVector = EyeVectorWorld * strMatrix;
#endif

gl_Position = ftransform();
ProjVector = gl_Position;
#ifdef APPLY_CLIPPING
#ifdef __GLSL_CG_DATA_TYPES
gl_ClipVertex = gl_ModelViewMatrix * gl_Vertex;
#endif
#endif
}

#endif // VERTEX_SHADER


#ifdef FRAGMENT_SHADER
// Fragment shader

#ifdef APPLY_DUDV
uniform sampler2D DuDvMapTexture;
#endif

#ifdef APPLY_EYEDOT
uniform sampler2D NormalmapTexture;
#endif
uniform sampler2D ReflectionTexture;
uniform sampler2D RefractionTexture;
uniform float TextureWidth, TextureHeight;

void main(void)
{
myhalf3 color;

#ifdef APPLY_DUDV
vec3 displacement = vec3(texture2D(DuDvMapTexture, vec2(TexCoord.pq) * vec2(0.25)));
vec2 coord = vec2(TexCoord.st) + vec2(displacement) * vec2 (0.2);

vec3 fdist = vec3 (normalize(vec3(texture2D(DuDvMapTexture, coord)) - vec3 (0.5))) * vec3(0.005);
#else
vec3 fdist = vec3(0.0);
#endif

// get projective texcoords
float scale = float(1.0 / float(ProjVector.w));
float inv2NW = 1.0 / (2.0 * float (TextureWidth));
float inv2NH = 1.0 / (2.0 * float (TextureHeight));
vec2 projCoord = (vec2(ProjVector.xy) * scale + vec2 (1.0)) * vec2 (0.5) + vec2(fdist.xy);
projCoord.s = float (clamp (float(projCoord.s), inv2NW, 1.0 - inv2NW));
projCoord.t = float (clamp (float(projCoord.t), inv2NH, 1.0 - inv2NH));


myhalf3 refr = myhalf3(0.0);
myhalf3 refl = myhalf3(0.0);

#ifdef APPLY_EYEDOT
// calculate dot product between the surface normal and eye vector
// great for simulating varying water translucency based on the view angle
myhalf3 surfaceNormal = normalize(myhalf3(texture2D(NormalmapTexture, coord)) - myhalf3 (0.5));
vec3 eyeNormal = normalize(myhalf3(EyeVector));

float refrdot = float(dot(surfaceNormal, eyeNormal));
//refrdot = float (clamp (refrdot, 0.0, 1.0));
float refldot = 1.0 - refrdot;
// get refraction and reflection

#ifdef APPLY_REFRACTION
refr = (myhalf3(texture2D(RefractionTexture, projCoord))) * refrdot;
#endif
#ifdef APPLY_REFLECTION
refl = (myhalf3(texture2D(ReflectionTexture, projCoord))) * refldot;
#endif

#else

#ifdef APPLY_REFRACTION
refr = (myhalf3(texture2D(RefractionTexture, projCoord)));
#endif
#ifdef APPLY_REFLECTION
refl = (myhalf3(texture2D(ReflectionTexture, projCoord)));
#endif

#endif

// add reflection and refraction
#ifdef APPLY_DISTORTION_ALPHA
color = myhalf3(gl_Color.rgb) + myhalf3(mix (refr, refl, float(gl_Color.a)));
#else
color = myhalf3(gl_Color.rgb) + refr + refl;
#endif

#ifdef APPLY_GRAYSCALE
float grey = dot(color, myhalf3(0.299, 0.587, 0.114));
gl_FragColor = vec4(vec3(grey),1.0);
#else
gl_FragColor = vec4(vec3(color),1.0);
#endif
}

#endif // FRAGMENT_SHADER


