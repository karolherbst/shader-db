#define FRAGMENT_SHADER
#define APPLY_LIGHTSTYLE0
#define APPLY_FBLIGHTMAP
#define APPLY_SPECULAR
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

varying vec2 TexCoord;
#ifdef APPLY_LIGHTSTYLE0
varying vec4 LightmapTexCoord01;
#ifdef APPLY_LIGHTSTYLE2
varying vec4 LightmapTexCoord23;
#endif
#endif

#if defined(APPLY_SPECULAR) || defined(APPLY_OFFSETMAPPING) || defined(APPLY_RELIEFMAPPING)
varying vec3 EyeVector;
#endif

#ifdef APPLY_DIRECTIONAL_LIGHT
varying vec3 LightVector;
#endif

varying mat3 strMatrix; // directions of S/T/R texcoords (tangent, binormal, normal)

#ifdef VERTEX_SHADER
// Vertex shader

uniform vec3 EyeOrigin;

#ifdef APPLY_DIRECTIONAL_LIGHT
uniform vec3 LightDir;
#endif

void main()
{
gl_FrontColor = gl_Color;

TexCoord = vec2 (gl_TextureMatrix[0] * gl_MultiTexCoord0);

#ifdef APPLY_LIGHTSTYLE0
LightmapTexCoord01.st = gl_MultiTexCoord4.st;
#ifdef APPLY_LIGHTSTYLE1
LightmapTexCoord01.pq = gl_MultiTexCoord5.st;
#ifdef APPLY_LIGHTSTYLE2
LightmapTexCoord23.st = gl_MultiTexCoord6.st;
#ifdef APPLY_LIGHTSTYLE3
LightmapTexCoord23.pq = gl_MultiTexCoord7.st;
#endif
#endif
#endif
#endif

strMatrix[0] = gl_MultiTexCoord1.xyz;
strMatrix[2] = gl_Normal.xyz;
strMatrix[1] = gl_MultiTexCoord1.w * cross (strMatrix[2], strMatrix[0]);

#if defined(APPLY_SPECULAR) || defined(APPLY_OFFSETMAPPING) || defined(APPLY_RELIEFMAPPING)
vec3 EyeVectorWorld = EyeOrigin - gl_Vertex.xyz;
EyeVector = EyeVectorWorld * strMatrix;
#endif

#ifdef APPLY_DIRECTIONAL_LIGHT
LightVector = LightDir * strMatrix;
#endif

gl_Position = ftransform ();
#ifdef APPLY_CLIPPING
#ifdef __GLSL_CG_DATA_TYPES
gl_ClipVertex = gl_ModelViewMatrix * gl_Vertex;
#endif
#endif
}

#endif // VERTEX_SHADER


#ifdef FRAGMENT_SHADER
// Fragment shader

#ifdef APPLY_LIGHTSTYLE0
uniform sampler2D LightmapTexture0;
uniform float DeluxemapOffset0; // s-offset for LightmapTexCoord
uniform myhalf3 lsColor0; // lightstyle color

#ifdef APPLY_LIGHTSTYLE1
uniform sampler2D LightmapTexture1;
uniform float DeluxemapOffset1;
uniform myhalf3 lsColor1;

#ifdef APPLY_LIGHTSTYLE2
uniform sampler2D LightmapTexture2;
uniform float DeluxemapOffset2;
uniform myhalf3 lsColor2;

#ifdef APPLY_LIGHTSTYLE3
uniform sampler2D LightmapTexture3;
uniform float DeluxemapOffset3;
uniform myhalf3 lsColor3;

#endif
#endif
#endif
#endif

uniform sampler2D BaseTexture;
uniform sampler2D NormalmapTexture;
uniform sampler2D GlossTexture;
#ifdef APPLY_DECAL
uniform sampler2D DecalTexture;
#endif

#if defined(APPLY_OFFSETMAPPING) || defined(APPLY_RELIEFMAPPING)
uniform float OffsetMappingScale;
#endif

uniform myhalf3 LightAmbient;
#ifdef APPLY_DIRECTIONAL_LIGHT
uniform myhalf3 LightDiffuse;
#endif

uniform myhalf GlossIntensity; // gloss scaling factor
uniform myhalf GlossExponent; // gloss exponent factor

#if defined(APPLY_OFFSETMAPPING) || defined(APPLY_RELIEFMAPPING)
// The following reliefmapping and offsetmapping routine was taken from DarkPlaces
// The credit goes to LordHavoc (as always)
vec2 OffsetMapping(vec2 TexCoord)
{
#ifdef APPLY_RELIEFMAPPING
// 14 sample relief mapping: linear search and then binary search
// this basically steps forward a small amount repeatedly until it finds
// itself inside solid, then jitters forward and back using decreasing
// amounts to find the impact
//vec3 OffsetVector = vec3(EyeVector.xy * ((1.0 / EyeVector.z) * OffsetMappingScale) * vec2(-1, 1), -1);
//vec3 OffsetVector = vec3(normalize(EyeVector.xy) * OffsetMappingScale * vec2(-1, 1), -1);
vec3 OffsetVector = vec3(normalize(EyeVector).xy * OffsetMappingScale * vec2(-1, 1), -1);
vec3 RT = vec3(TexCoord, 1);
OffsetVector *= 0.1;
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector *  step(texture2D(NormalmapTexture, RT.xy).a, RT.z);
RT += OffsetVector * (step(texture2D(NormalmapTexture, RT.xy).a, RT.z)          - 0.5);
RT += OffsetVector * (step(texture2D(NormalmapTexture, RT.xy).a, RT.z) * 0.5    - 0.25);
RT += OffsetVector * (step(texture2D(NormalmapTexture, RT.xy).a, RT.z) * 0.25   - 0.125);
RT += OffsetVector * (step(texture2D(NormalmapTexture, RT.xy).a, RT.z) * 0.125  - 0.0625);
RT += OffsetVector * (step(texture2D(NormalmapTexture, RT.xy).a, RT.z) * 0.0625 - 0.03125);
return RT.xy;
#else
// 2 sample offset mapping (only 2 samples because of ATI Radeon 9500-9800/X300 limits)
// this basically moves forward the full distance, and then backs up based
// on height of samples
//vec2 OffsetVector = vec2(EyeVector.xy * ((1.0 / EyeVector.z) * OffsetMappingScale) * vec2(-1, 1));
//vec2 OffsetVector = vec2(normalize(EyeVector.xy) * OffsetMappingScale * vec2(-1, 1));
vec2 OffsetVector = vec2(normalize(EyeVector).xy * OffsetMappingScale * vec2(-1, 1));
TexCoord += OffsetVector;
OffsetVector *= 0.5;
TexCoord -= OffsetVector * texture2D(NormalmapTexture, TexCoord).a;
TexCoord -= OffsetVector * texture2D(NormalmapTexture, TexCoord).a;
return TexCoord;
#endif
}
#endif

void main()
{
#if defined(APPLY_OFFSETMAPPING) || defined(APPLY_RELIEFMAPPING)
// apply offsetmapping
vec2 TexCoordOffset = OffsetMapping(TexCoord);
#define TexCoord TexCoordOffset
#endif
myhalf3 surfaceNormal;
myhalf3 diffuseNormalModelspace;
myhalf3 diffuseNormal = myhalf3 (0.0, 0.0, -1.0);
float diffuseProduct;
#ifdef APPLY_CELLSHADING
int lightcell;
float diffuseProductPositive;
float diffuseProductNegative;
float hardShadow;
#endif

myhalf3 weightedDiffuseNormal;
myhalf3 specularNormal;
float specularProduct;

#if !defined(APPLY_DIRECTIONAL_LIGHT) && !defined(APPLY_LIGHTSTYLE0)
myhalf4 color = myhalf4 (1.0, 1.0, 1.0, 1.0);
#else
myhalf4 color = myhalf4 (0.0, 0.0, 0.0, 1.0);
#endif

// get the surface normal
surfaceNormal = normalize (myhalf3 (texture2D (NormalmapTexture, TexCoord)) - myhalf3 (0.5));

#ifdef APPLY_DIRECTIONAL_LIGHT
diffuseNormal = myhalf3 (LightVector);
weightedDiffuseNormal = diffuseNormal;
diffuseProduct = float (dot (surfaceNormal, diffuseNormal));
#ifdef APPLY_CELLSHADING
hardShadow = 0.0;
diffuseProductPositive = max (diffuseProduct, 0.0);
diffuseProductNegative = (-min (diffuseProduct, 0.0) - 0.3);

// smooth the hard shadow edge
lightcell = int(max(diffuseProduct + 0.1, 0.0) * 2.0);
hardShadow += float(lightcell);

lightcell = int(max(diffuseProduct + 0.055, 0.0) * 2.0);
hardShadow += float(lightcell);

lightcell = int(diffuseProductPositive * 2.0);
hardShadow += float(lightcell);

color.rgb += myhalf(0.6 + hardShadow * 0.3333333333 * 0.27 + diffuseProductPositive * 0.14);

// backlight
lightcell = int (diffuseProductNegative * 2.0);
color.rgb += myhalf (float(lightcell) * 0.085 + diffuseProductNegative * 0.085);
#else
color.rgb += LightDiffuse.rgb * myhalf(max (diffuseProduct, 0.0)) + LightAmbient.rgb;
#endif

#endif

// deluxemapping using light vectors in modelspace

#ifdef APPLY_LIGHTSTYLE0

// get light normal
diffuseNormalModelspace = myhalf3 (texture2D(LightmapTexture0, vec2(LightmapTexCoord01.s+DeluxemapOffset0,LightmapTexCoord01.t))) - myhalf3 (0.5);
diffuseNormal = normalize (myhalf3(dot(diffuseNormalModelspace,myhalf3(strMatrix[0])),dot(diffuseNormalModelspace,myhalf3(strMatrix[1])),dot(diffuseNormalModelspace,myhalf3(strMatrix[2]))));
// calculate directional shading
diffuseProduct = float (dot (surfaceNormal, diffuseNormal));

#ifdef APPLY_FBLIGHTMAP
weightedDiffuseNormal = diffuseNormal;
// apply lightmap color
color.rgb += myhalf3 (max (diffuseProduct, 0.0) * myhalf3 (texture2D (LightmapTexture0, LightmapTexCoord01.st)));
#else

#define NORMALIZE_DIFFUSE_NORMAL

weightedDiffuseNormal = lsColor0 * diffuseNormal;
// apply lightmap color
color.rgb += lsColor0 * myhalf(max (diffuseProduct, 0.0)) * myhalf3 (texture2D (LightmapTexture0, LightmapTexCoord01.st));
#endif

#ifdef APPLY_AMBIENT_COMPENSATION
// compensate for ambient lighting
color.rgb += myhalf((1.0 - max (diffuseProduct, 0.0))) * LightAmbient;
#endif

#ifdef APPLY_LIGHTSTYLE1
diffuseNormalModelspace = myhalf3 (texture2D (LightmapTexture1, vec2(LightmapTexCoord01.p+DeluxemapOffset1,LightmapTexCoord01.q))) - myhalf3 (0.5);
diffuseNormal = normalize (myhalf3(dot(diffuseNormalModelspace,myhalf3(strMatrix[0])),dot(diffuseNormalModelspace,myhalf3(strMatrix[1])),dot(diffuseNormalModelspace,myhalf3(strMatrix[2]))));
diffuseProduct = float (dot (surfaceNormal, diffuseNormal));
weightedDiffuseNormal += lsColor1 * diffuseNormal;
color.rgb += lsColor1 * myhalf(max (diffuseProduct, 0.0)) * myhalf3 (texture2D (LightmapTexture1, LightmapTexCoord01.pq));

#ifdef APPLY_LIGHTSTYLE2
diffuseNormalModelspace = myhalf3 (texture2D (LightmapTexture2, vec2(LightmapTexCoord23.s+DeluxemapOffset2,LightmapTexCoord23.t))) - myhalf3 (0.5);
diffuseNormal = normalize (myhalf3(dot(diffuseNormalModelspace,myhalf3(strMatrix[0])),dot(diffuseNormalModelspace,myhalf3(strMatrix[1])),dot(diffuseNormalModelspace,myhalf3(strMatrix[2]))));
diffuseProduct = float (dot (surfaceNormal, diffuseNormal));
weightedDiffuseNormal += lsColor2 * diffuseNormal;
color.rgb += lsColor2 * myhalf(max (diffuseProduct, 0.0)) * myhalf3 (texture2D (LightmapTexture2, LightmapTexCoord23.st));

#ifdef APPLY_LIGHTSTYLE3
diffuseNormalModelspace = myhalf3 (texture2D (LightmapTexture3, vec2(LightmapTexCoord23.p+DeluxemapOffset3,LightmapTexCoord23.q))) - myhalf3 (0.5);;
diffuseNormal = normalize (myhalf3(dot(diffuseNormalModelspace,myhalf3(strMatrix[0])),dot(diffuseNormalModelspace,myhalf3(strMatrix[1])),dot(diffuseNormalModelspace,myhalf3(strMatrix[2]))));
diffuseProduct = float (dot (surfaceNormal, diffuseNormal));
weightedDiffuseNormal += lsColor3 * diffuseNormal;
color.rgb += lsColor3 * myhalf(max (diffuseProduct, 0.0)) * myhalf3 (texture2D (LightmapTexture3, LightmapTexCoord23.pq));

#endif
#endif
#endif
#endif

#ifdef APPLY_SPECULAR

#ifdef NORMALIZE_DIFFUSE_NORMAL
specularNormal = normalize (myhalf3 (normalize (weightedDiffuseNormal)) + myhalf3 (normalize (EyeVector)));
#else
specularNormal = normalize (weightedDiffuseNormal + myhalf3 (normalize (EyeVector)));
#endif

specularProduct = float (dot (surfaceNormal, specularNormal));
color.rgb += (myhalf3(texture2D(GlossTexture, TexCoord)) * GlossIntensity) * pow(myhalf(max(specularProduct, 0.0)), GlossExponent);
#endif

#ifdef APPLY_BASETEX_ALPHA_ONLY
color = min(color, myhalf4(texture2D(BaseTexture, TexCoord).a));
#else
#ifdef APPLY_COLOR_CLAMPING
color = min(color, myhalf4(1.0));
#endif
color = color * myhalf4(texture2D(BaseTexture, TexCoord));
#endif

#ifdef APPLY_DECAL
#ifdef APPLY_DECAL_ADD
myhalf3 decal = myhalf3(gl_Color.rgb) * myhalf3(texture2D(DecalTexture, TexCoord));
color.rgb = decal.rgb + color.rgb;
color.a = color.a * myhalf(gl_Color.a);
#else
myhalf4 decal = myhalf4(gl_Color.rgba);
if (decal.a > 0.0)
{
decal = decal * myhalf4(texture2D(DecalTexture, TexCoord));
color.rgb = decal.rgb * decal.a + color.rgb * (1.0-decal.a);
}
#endif
#else
color = color * myhalf4(gl_Color.rgba);
#endif

#ifdef APPLY_GRAYSCALE
float grey = dot(color, myhalf3(0.299, 0.587, 0.114));
gl_FragColor = vec4(vec3(grey),color.a);
#else
gl_FragColor = vec4(color);
#endif
}

#endif // FRAGMENT_SHADER


