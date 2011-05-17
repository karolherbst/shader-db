#define VERTEX_SHADER
#define MODE_LIGHTDIRECTIONMAP_MODELSPACE
#define USEDIFFUSE





#define USESPECULAR
#define USEPOSTPROCESSING

#define USEOFFSETMAPPING








// ambient+diffuse+specular+normalmap+attenuation+cubemap+fog shader
// written by Forest 'LordHavoc' Hale

// enable various extensions depending on permutation:

#ifdef USESHADOWMAPRECT
# extension GL_ARB_texture_rectangle : enable
#endif

#ifdef USESHADOWMAP2D
# ifdef GL_EXT_gpu_shader4
#   extension GL_EXT_gpu_shader4 : enable
# endif
# ifdef GL_ARB_texture_gather
#   extension GL_ARB_texture_gather : enable
# else
#   ifdef GL_AMD_texture_texture4
#     extension GL_AMD_texture_texture4 : enable
#   endif
# endif
#endif

#ifdef USESHADOWMAPCUBE
# extension GL_EXT_gpu_shader4 : enable
#endif

#ifdef USESHADOWSAMPLER
# extension GL_ARB_shadow : enable
#endif

// common definitions between vertex shader and fragment shader:

//#ifdef __GLSL_CG_DATA_TYPES
//# define myhalf half
//# define myhalf2 half2
//# define myhalf3half3
//# define myhalf4 half4
//#else
# define myhalf float
# define myhalf2 vec2
# define myhalf3 vec3
# define myhalf4 vec4
//#endif

#ifdef MODE_DEPTH_OR_SHADOW

# ifdef VERTEX_SHADER
void main(void)
{
	gl_Position = ftransform();
}
# endif

#else
#ifdef MODE_SHOWDEPTH
# ifdef VERTEX_SHADER
void main(void)
{
	gl_Position = ftransform();
	gl_FrontColor = vec4(gl_Position.z, gl_Position.z, gl_Position.z, 1.0);
}
# endif
# ifdef FRAGMENT_SHADER
void main(void)
{
	gl_FragColor = gl_Color;
}
# endif

#else // !MODE_SHOWDEPTH

#ifdef MODE_POSTPROCESS
# ifdef VERTEX_SHADER
void main(void)
{
	gl_FrontColor = gl_Color;
	gl_Position = ftransform();
	gl_TexCoord[0] = gl_TextureMatrix[0] * gl_MultiTexCoord0;
#ifdef USEBLOOM
	gl_TexCoord[1] = gl_TextureMatrix[1] * gl_MultiTexCoord1;
#endif
}
# endif
# ifdef FRAGMENT_SHADER

uniform sampler2D Texture_First;
#ifdef USEBLOOM
uniform sampler2D Texture_Second;
#endif
#ifdef USEGAMMARAMPS
uniform sampler2D Texture_GammaRamps;
#endif
#ifdef USESATURATION
uniform float Saturation;
#endif
#ifdef USEVIEWTINT
uniform vec4 TintColor;
#endif
//uncomment these if you want to use them:
uniform vec4 UserVec1;
// uniform vec4 UserVec2;
// uniform vec4 UserVec3;
// uniform vec4 UserVec4;
// uniform float ClientTime;
uniform vec2 PixelSize;
void main(void)
{
	gl_FragColor = texture2D(Texture_First, gl_TexCoord[0].xy);
#ifdef USEBLOOM
	gl_FragColor += texture2D(Texture_Second, gl_TexCoord[1].xy);
#endif
#ifdef USEVIEWTINT
	gl_FragColor = mix(gl_FragColor, TintColor, TintColor.a);
#endif

#ifdef USEPOSTPROCESSING
// do r_glsl_dumpshader, edit glsl/default.glsl, and replace this by your own postprocessing if you want
// this code does a blur with the radius specified in the first component of r_glsl_postprocess_uservec1 and blends it using the second component
	gl_FragColor += texture2D(Texture_First, gl_TexCoord[0].xy + PixelSize*UserVec1.x*vec2(-0.987688, -0.156434)) * UserVec1.y;
	gl_FragColor += texture2D(Texture_First, gl_TexCoord[0].xy + PixelSize*UserVec1.x*vec2(-0.156434, -0.891007)) * UserVec1.y;
	gl_FragColor += texture2D(Texture_First, gl_TexCoord[0].xy + PixelSize*UserVec1.x*vec2( 0.891007, -0.453990)) * UserVec1.y;
	gl_FragColor += texture2D(Texture_First, gl_TexCoord[0].xy + PixelSize*UserVec1.x*vec2( 0.707107,  0.707107)) * UserVec1.y;
	gl_FragColor += texture2D(Texture_First, gl_TexCoord[0].xy + PixelSize*UserVec1.x*vec2(-0.453990,  0.891007)) * UserVec1.y;
	gl_FragColor /= (1 + 5 * UserVec1.y);
#endif

#ifdef USESATURATION
	//apply saturation BEFORE gamma ramps, so v_glslgamma value does not matter
	myhalf y = dot(gl_FragColor.rgb, vec3(0.299, 0.587, 0.114));
	//gl_FragColor = vec3(y) + (gl_FragColor.rgb - vec3(y)) * Saturation;
	gl_FragColor.rgb = mix(vec3(y), gl_FragColor.rgb, Saturation);
#endif

#ifdef USEGAMMARAMPS
	gl_FragColor.r = texture2D(Texture_GammaRamps, vec2(gl_FragColor.r, 0)).r;
	gl_FragColor.g = texture2D(Texture_GammaRamps, vec2(gl_FragColor.g, 0)).g;
	gl_FragColor.b = texture2D(Texture_GammaRamps, vec2(gl_FragColor.b, 0)).b;
#endif
}
# endif


#else
#ifdef MODE_GENERIC
# ifdef VERTEX_SHADER
void main(void)
{
	gl_FrontColor = gl_Color;
#  ifdef USEDIFFUSE
	gl_TexCoord[0] = gl_TextureMatrix[0] * gl_MultiTexCoord0;
#  endif
#  ifdef USESPECULAR
	gl_TexCoord[1] = gl_TextureMatrix[1] * gl_MultiTexCoord1;
#  endif
	gl_Position = ftransform();
}
# endif
# ifdef FRAGMENT_SHADER

#  ifdef USEDIFFUSE
uniform sampler2D Texture_First;
#  endif
#  ifdef USESPECULAR
uniform sampler2D Texture_Second;
#  endif

void main(void)
{
	gl_FragColor = gl_Color;
#  ifdef USEDIFFUSE
	gl_FragColor *= texture2D(Texture_First, gl_TexCoord[0].xy);
#  endif

#  ifdef USESPECULAR
	vec4 tex2 = texture2D(Texture_Second, gl_TexCoord[1].xy);
#  endif
#  ifdef USECOLORMAPPING
	gl_FragColor *= tex2;
#  endif
#  ifdef USEGLOW
	gl_FragColor += tex2;
#  endif
#  ifdef USEVERTEXTEXTUREBLEND
	gl_FragColor = mix(gl_FragColor, tex2, tex2.a);
#  endif
}
# endif

#else // !MODE_GENERIC

varying vec2 TexCoord;
#ifdef USEVERTEXTEXTUREBLEND
varying vec2 TexCoord2;
#endif
varying vec2 TexCoordLightmap;

#ifdef MODE_LIGHTSOURCE
varying vec3 CubeVector;
#endif

#ifdef MODE_LIGHTSOURCE
varying vec3 LightVector;
#endif
#ifdef MODE_LIGHTDIRECTION
varying vec3 LightVector;
#endif

varying vec3 EyeVector;
#ifdef USEFOG
varying vec3 EyeVectorModelSpace;
#endif

varying vec3 VectorS; // direction of S texcoord (sometimes crudely called tangent)
varying vec3 VectorT; // direction of T texcoord (sometimes crudely called binormal)
varying vec3 VectorR; // direction of R texcoord (surface normal)

#ifdef MODE_WATER
varying vec4 ModelViewProjectionPosition;
#endif
#ifdef MODE_REFRACTION
varying vec4 ModelViewProjectionPosition;
#endif
#ifdef USEREFLECTION
varying vec4 ModelViewProjectionPosition;
#endif





// vertex shader specific:
#ifdef VERTEX_SHADER

uniform vec3 LightPosition;
uniform vec3 EyePosition;
uniform vec3 LightDir;

// TODO: get rid of tangentt (texcoord2) and use a crossproduct to regenerate it from tangents (texcoord1) and normal (texcoord3), this would require sending a 4 component texcoord1 with W as 1 or -1 according to which side the texcoord2 should be on

void main(void)
{
	gl_FrontColor = gl_Color;
	// copy the surface texcoord
	TexCoord = vec2(gl_TextureMatrix[0] * gl_MultiTexCoord0);
#ifdef USEVERTEXTEXTUREBLEND
	TexCoord2 = vec2(gl_TextureMatrix[1] * gl_MultiTexCoord0);
#endif
#ifndef MODE_LIGHTSOURCE
# ifndef MODE_LIGHTDIRECTION
	TexCoordLightmap = vec2(gl_MultiTexCoord4);
# endif
#endif

#ifdef MODE_LIGHTSOURCE
	// transform vertex position into light attenuation/cubemap space
	// (-1 to +1 across the light box)
	CubeVector = vec3(gl_TextureMatrix[3] * gl_Vertex);

	// transform unnormalized light direction into tangent space
	// (we use unnormalized to ensure that it interpolates correctly and then
	//  normalize it per pixel)
	vec3 lightminusvertex = LightPosition - gl_Vertex.xyz;
	LightVector.x = dot(lightminusvertex, gl_MultiTexCoord1.xyz);
	LightVector.y = dot(lightminusvertex, gl_MultiTexCoord2.xyz);
	LightVector.z = dot(lightminusvertex, gl_MultiTexCoord3.xyz);
#endif

#ifdef MODE_LIGHTDIRECTION
	LightVector.x = dot(LightDir, gl_MultiTexCoord1.xyz);
	LightVector.y = dot(LightDir, gl_MultiTexCoord2.xyz);
	LightVector.z = dot(LightDir, gl_MultiTexCoord3.xyz);
#endif

	// transform unnormalized eye direction into tangent space
#ifndef USEFOG
	vec3 EyeVectorModelSpace;
#endif
	EyeVectorModelSpace = EyePosition - gl_Vertex.xyz;
	EyeVector.x = dot(EyeVectorModelSpace, gl_MultiTexCoord1.xyz);
	EyeVector.y = dot(EyeVectorModelSpace, gl_MultiTexCoord2.xyz);
	EyeVector.z = dot(EyeVectorModelSpace, gl_MultiTexCoord3.xyz);

#ifdef MODE_LIGHTDIRECTIONMAP_MODELSPACE
	VectorS = gl_MultiTexCoord1.xyz;
	VectorT = gl_MultiTexCoord2.xyz;
	VectorR = gl_MultiTexCoord3.xyz;
#endif

//#if defined(MODE_WATER) || defined(MODE_REFRACTION) || defined(USEREFLECTION)
//	ModelViewProjectionPosition = gl_Vertex * gl_ModelViewProjectionMatrix;
//	//ModelViewProjectionPosition_svector = (gl_Vertex + vec4(gl_MultiTexCoord1.xyz, 0)) * gl_ModelViewProjectionMatrix - ModelViewProjectionPosition;
//	//ModelViewProjectionPosition_tvector = (gl_Vertex + vec4(gl_MultiTexCoord2.xyz, 0)) * gl_ModelViewProjectionMatrix - ModelViewProjectionPosition;
//#endif

// transform vertex to camera space, using ftransform to match non-VS
	// rendering
	gl_Position = ftransform();

#ifdef MODE_WATER
	ModelViewProjectionPosition = gl_Position;
#endif
#ifdef MODE_REFRACTION
	ModelViewProjectionPosition = gl_Position;
#endif
#ifdef USEREFLECTION
	ModelViewProjectionPosition = gl_Position;
#endif
}

#endif // VERTEX_SHADER




// fragment shader specific:
#ifdef FRAGMENT_SHADER

// 13 textures, we can only use up to 16 on DX9-class hardware
uniform sampler2D Texture_Normal;
uniform sampler2D Texture_Color;
uniform sampler2D Texture_Gloss;
uniform sampler2D Texture_Glow;
uniform sampler2D Texture_SecondaryNormal;
uniform sampler2D Texture_SecondaryColor;
uniform sampler2D Texture_SecondaryGloss;
uniform sampler2D Texture_SecondaryGlow;
uniform sampler2D Texture_Pants;
uniform sampler2D Texture_Shirt;
uniform sampler2D Texture_FogMask;
uniform sampler2D Texture_Lightmap;
uniform sampler2D Texture_Deluxemap;
uniform sampler2D Texture_Refraction;
uniform sampler2D Texture_Reflection;
uniform sampler2D Texture_Attenuation;
uniform samplerCube Texture_Cube;

#define showshadowmap 0

#ifdef USESHADOWMAPRECT
# ifdef USESHADOWSAMPLER
uniform sampler2DRectShadow Texture_ShadowMapRect;
# else
uniform sampler2DRect Texture_ShadowMapRect;
# endif
#endif

#ifdef USESHADOWMAP2D
# ifdef USESHADOWSAMPLER
uniform sampler2DShadow Texture_ShadowMap2D;
# else
uniform sampler2D Texture_ShadowMap2D;
# endif
#endif

#ifdef USESHADOWMAPVSDCT
uniform samplerCube Texture_CubeProjection;
#endif

#ifdef USESHADOWMAPCUBE
# ifdef USESHADOWSAMPLER
uniform samplerCubeShadow Texture_ShadowMapCube;
# else
uniform samplerCube Texture_ShadowMapCube;
# endif
#endif

uniform myhalf3 LightColor;
uniform myhalf3 AmbientColor;
uniform myhalf3 DiffuseColor;
uniform myhalf3 SpecularColor;
uniform myhalf3 Color_Pants;
uniform myhalf3 Color_Shirt;
uniform myhalf3 FogColor;

uniform myhalf4 TintColor;


//#ifdef MODE_WATER
uniform vec4 DistortScaleRefractReflect;
uniform vec4 ScreenScaleRefractReflect;
uniform vec4 ScreenCenterRefractReflect;
uniform myhalf4 RefractColor;
uniform myhalf4 ReflectColor;
uniform myhalf ReflectFactor;
uniform myhalf ReflectOffset;
//#else
//# ifdef MODE_REFRACTION
//uniform vec4 DistortScaleRefractReflect;
//uniform vec4 ScreenScaleRefractReflect;
//uniform vec4 ScreenCenterRefractReflect;
//uniform myhalf4 RefractColor;
//#  ifdef USEREFLECTION
//uniform myhalf4 ReflectColor;
//#  endif
//# else
//#  ifdef USEREFLECTION
//uniform vec4 DistortScaleRefractReflect;
//uniform vec4 ScreenScaleRefractReflect;
//uniform vec4 ScreenCenterRefractReflect;
//uniform myhalf4 ReflectColor;
//#  endif
//# endif
//#endif

uniform myhalf GlowScale;
uniform myhalf SceneBrightness;

uniform float OffsetMapping_Scale;
uniform float OffsetMapping_Bias;
uniform float FogRangeRecip;

uniform myhalf AmbientScale;
uniform myhalf DiffuseScale;
uniform myhalf SpecularScale;
uniform myhalf SpecularPower;

#ifdef USEOFFSETMAPPING
vec2 OffsetMapping(vec2 TexCoord)
{
#ifdef USEOFFSETMAPPING_RELIEFMAPPING
	// 14 sample relief mapping: linear search and then binary search
	// this basically steps forward a small amount repeatedly until it finds
	// itself inside solid, then jitters forward and back using decreasing
	// amounts to find the impact
	//vec3 OffsetVector = vec3(EyeVector.xy * ((1.0 / EyeVector.z) * OffsetMapping_Scale) * vec2(-1, 1), -1);
	//vec3 OffsetVector = vec3(normalize(EyeVector.xy) * OffsetMapping_Scale * vec2(-1, 1), -1);
	vec3 OffsetVector = vec3(normalize(EyeVector).xy * OffsetMapping_Scale * vec2(-1, 1), -1);
	vec3 RT = vec3(TexCoord, 1);
	OffsetVector *= 0.1;
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector *  step(texture2D(Texture_Normal, RT.xy).a, RT.z);
	RT += OffsetVector * (step(texture2D(Texture_Normal, RT.xy).a, RT.z)          - 0.5);
	RT += OffsetVector * (step(texture2D(Texture_Normal, RT.xy).a, RT.z) * 0.5    - 0.25);
	RT += OffsetVector * (step(texture2D(Texture_Normal, RT.xy).a, RT.z) * 0.25   - 0.125);
	RT += OffsetVector * (step(texture2D(Texture_Normal, RT.xy).a, RT.z) * 0.125  - 0.0625);
	RT += OffsetVector * (step(texture2D(Texture_Normal, RT.xy).a, RT.z) * 0.0625 - 0.03125);
	return RT.xy;
#else
	// 3 sample offset mapping (only 3 samples because of ATI Radeon 9500-9800/X300 limits)
	// this basically moves forward the full distance, and then backs up based
	// on height of samples
	//vec2 OffsetVector = vec2(EyeVector.xy * ((1.0 / EyeVector.z) * OffsetMapping_Scale) * vec2(-1, 1));
	//vec2 OffsetVector = vec2(normalize(EyeVector.xy) * OffsetMapping_Scale * vec2(-1, 1));
	vec2 OffsetVector = vec2(normalize(EyeVector).xy * OffsetMapping_Scale * vec2(-1, 1));
	TexCoord += OffsetVector;
	OffsetVector *= 0.333;
	TexCoord -= OffsetVector * texture2D(Texture_Normal, TexCoord).a;
	TexCoord -= OffsetVector * texture2D(Texture_Normal, TexCoord).a;
	TexCoord -= OffsetVector * texture2D(Texture_Normal, TexCoord).a;
	return TexCoord;
#endif
}
#endif // USEOFFSETMAPPING

#if defined(USESHADOWMAPRECT) || defined(USESHADOWMAP2D) || defined(USESHADOWMAPCUBE)
uniform vec2 ShadowMap_TextureScale;
uniform vec4 ShadowMap_Parameters;
#endif

#if defined(USESHADOWMAPRECT) || defined(USESHADOWMAP2D)
vec3 GetShadowMapTC2D(vec3 dir)
{
	vec3 adir = abs(dir);
# ifndef USESHADOWMAPVSDCT
	vec2 tc;
	vec2 offset;
	float ma;
	if (adir.x > adir.y)
	{
		if (adir.x > adir.z) // X
		{
			ma = adir.x;
			tc = dir.zy;
			offset = vec2(mix(0.5, 1.5, dir.x < 0.0), 0.5);
		}
		else // Z
		{
			ma = adir.z;
			tc = dir.xy;
			offset = vec2(mix(0.5, 1.5, dir.z < 0.0), 2.5);
		}
	}
	else
	{
		if (adir.y > adir.z) // Y
		{
			ma = adir.y;
			tc = dir.xz;
			offset = vec2(mix(0.5, 1.5, dir.y < 0.0), 1.5);
		}
		else // Z
		{
			ma = adir.z;
			tc = dir.xy;
			offset = vec2(mix(0.5, 1.5, dir.z < 0.0), 2.5);
		}
	}

	vec3 stc = vec3(tc * ShadowMap_Parameters.x, ShadowMap_Parameters.w) / ma;
	stc.xy += offset * ShadowMap_Parameters.y;
	stc.z += ShadowMap_Parameters.z;
#  if showshadowmap
	stc.xy *= ShadowMap_TextureScale;
#  endif
	return stc;
# else
	vec4 proj = textureCube(Texture_CubeProjection, dir);
	float ma = max(max(adir.x, adir.y), adir.z);
	vec3 stc = vec3(mix(dir.xy, dir.zz, proj.xy) * ShadowMap_Parameters.x, ShadowMap_Parameters.w) / ma;
	stc.xy += proj.zw * ShadowMap_Parameters.y;
	stc.z += ShadowMap_Parameters.z;
#  if showshadowmap
	stc.xy *= ShadowMap_TextureScale;
#  endif
	return stc;
# endif
}
#endif // defined(USESHADOWMAPRECT) || defined(USESHADOWMAP2D)

#ifdef USESHADOWMAPCUBE
vec4 GetShadowMapTCCube(vec3 dir)
{
    vec3 adir = abs(dir);
    return vec4(dir, ShadowMap_Parameters.z + ShadowMap_Parameters.w / max(max(adir.x, adir.y), adir.z));
}
#endif

#if !showshadowmap
# ifdef USESHADOWMAPRECT
float ShadowMapCompare(vec3 dir)
{
	vec3 shadowmaptc = GetShadowMapTC2D(dir);
	float f;
#  ifdef USESHADOWSAMPLER

#    ifdef USESHADOWMAPPCF
#      define texval(x, y) shadow2DRect(Texture_ShadowMapRect, shadowmaptc + vec3(x, y, 0.0)).r
    f = dot(vec4(0.25), vec4(texval(-0.4, 1.0), texval(-1.0, -0.4), texval(0.4, -1.0), texval(1.0, 0.4)));
#    else
    f = shadow2DRect(Texture_ShadowMapRect, shadowmaptc).r;
#    endif

#  else

#    ifdef USESHADOWMAPPCF
#      if USESHADOWMAPPCF > 1
#        define texval(x, y) texture2DRect(Texture_ShadowMapRect, center + vec2(x, y)).r
    vec2 center = shadowmaptc.xy - 0.5, offset = fract(center);
    vec4 row1 = step(shadowmaptc.z, vec4(texval(-1.0, -1.0), texval( 0.0, -1.0), texval( 1.0, -1.0), texval( 2.0, -1.0)));
    vec4 row2 = step(shadowmaptc.z, vec4(texval(-1.0,  0.0), texval( 0.0,  0.0), texval( 1.0,  0.0), texval( 2.0,  0.0)));
    vec4 row3 = step(shadowmaptc.z, vec4(texval(-1.0,  1.0), texval( 0.0,  1.0), texval( 1.0,  1.0), texval( 2.0,  1.0)));
    vec4 row4 = step(shadowmaptc.z, vec4(texval(-1.0,  2.0), texval( 0.0,  2.0), texval( 1.0,  2.0), texval( 2.0,  2.0)));
    vec4 cols = row2 + row3 + mix(row1, row4, offset.y);
    f = dot(mix(cols.xyz, cols.yzw, offset.x), vec3(1.0/9.0));
#      else
#        define texval(x, y) texture2DRect(Texture_ShadowMapRect, shadowmaptc.xy + vec2(x, y)).r
    vec2 offset = fract(shadowmaptc.xy);
    vec3 row1 = step(shadowmaptc.z, vec3(texval(-1.0, -1.0), texval( 0.0, -1.0), texval( 1.0, -1.0)));
    vec3 row2 = step(shadowmaptc.z, vec3(texval(-1.0,  0.0), texval( 0.0,  0.0), texval( 1.0,  0.0)));
    vec3 row3 = step(shadowmaptc.z, vec3(texval(-1.0,  1.0), texval( 0.0,  1.0), texval( 1.0,  1.0)));
    vec3 cols = row2 + mix(row1, row3, offset.y);
    f = dot(mix(cols.xy, cols.yz, offset.x), vec2(0.25));
#      endif
#    else
    f = step(shadowmaptc.z, texture2DRect(Texture_ShadowMapRect, shadowmaptc.xy).r);
#    endif

#  endif
	return f;
}
# endif

# ifdef USESHADOWMAP2D
float ShadowMapCompare(vec3 dir)
{
    vec3 shadowmaptc = GetShadowMapTC2D(dir);
    float f;

#  ifdef USESHADOWSAMPLER
#    ifdef USESHADOWMAPPCF
#      define texval(x, y) shadow2D(Texture_ShadowMap2D, vec3(center + vec2(x, y)*ShadowMap_TextureScale, shadowmaptc.z)).r  
    vec2 center = shadowmaptc.xy*ShadowMap_TextureScale;
    f = dot(vec4(0.25), vec4(texval(-0.4, 1.0), texval(-1.0, -0.4), texval(0.4, -1.0), texval(1.0, 0.4)));
#    else
    f = shadow2D(Texture_ShadowMap2D, vec3(shadowmaptc.xy*ShadowMap_TextureScale, shadowmaptc.z)).r;
#    endif
#  else
#    ifdef USESHADOWMAPPCF
#     if defined(GL_ARB_texture_gather) || defined(GL_AMD_texture_texture4)
#      ifdef GL_ARB_texture_gather
#        define texval(x, y) textureGatherOffset(Texture_ShadowMap2D, center, ivec(x, y))
#      else
#        define texval(x, y) texture4(Texture_ShadowMap2D, center + vec2(x,y)*ShadowMap_TextureScale)
#      endif
    vec2 center = shadowmaptc.xy - 0.5, offset = fract(center);
    center *= ShadowMap_TextureScale;
    vec4 group1 = step(shadowmaptc.z, texval(-1.0, -1.0));
    vec4 group2 = step(shadowmaptc.z, texval( 1.0, -1.0));
    vec4 group3 = step(shadowmaptc.z, texval(-1.0,  1.0));
    vec4 group4 = step(shadowmaptc.z, texval( 1.0,  1.0));
    vec4 cols = vec4(group1.rg, group2.rg) + vec4(group3.ab, group4.ab) +
                mix(vec4(group1.ab, group2.ab), vec4(group3.rg, group4.rg), offset.y);
    f = dot(mix(cols.xyz, cols.yzw, offset.x), vec3(1.0/9.0));
#     else
#      ifdef GL_EXT_gpu_shader4
#        define texval(x, y) texture2DOffset(Texture_ShadowMap2D, center, ivec2(x, y)).r
#      else
#        define texval(x, y) texture2D(Texture_ShadowMap2D, center + vec2(x, y)*ShadowMap_TextureScale).r  
#      endif
#      if USESHADOWMAPPCF > 1
    vec2 center = shadowmaptc.xy - 0.5, offset = fract(center);
    center *= ShadowMap_TextureScale;
    vec4 row1 = step(shadowmaptc.z, vec4(texval(-1.0, -1.0), texval( 0.0, -1.0), texval( 1.0, -1.0), texval( 2.0, -1.0)));
    vec4 row2 = step(shadowmaptc.z, vec4(texval(-1.0,  0.0), texval( 0.0,  0.0), texval( 1.0,  0.0), texval( 2.0,  0.0)));
    vec4 row3 = step(shadowmaptc.z, vec4(texval(-1.0,  1.0), texval( 0.0,  1.0), texval( 1.0,  1.0), texval( 2.0,  1.0)));
    vec4 row4 = step(shadowmaptc.z, vec4(texval(-1.0,  2.0), texval( 0.0,  2.0), texval( 1.0,  2.0), texval( 2.0,  2.0)));
    vec4 cols = row2 + row3 + mix(row1, row4, offset.y);
    f = dot(mix(cols.xyz, cols.yzw, offset.x), vec3(1.0/9.0));
#      else
    vec2 center = shadowmaptc.xy*ShadowMap_TextureScale, offset = fract(shadowmaptc.xy);
    vec3 row1 = step(shadowmaptc.z, vec3(texval(-1.0, -1.0), texval( 0.0, -1.0), texval( 1.0, -1.0)));
    vec3 row2 = step(shadowmaptc.z, vec3(texval(-1.0,  0.0), texval( 0.0,  0.0), texval( 1.0,  0.0)));
    vec3 row3 = step(shadowmaptc.z, vec3(texval(-1.0,  1.0), texval( 0.0,  1.0), texval( 1.0,  1.0)));
    vec3 cols = row2 + mix(row1, row3, offset.y);
    f = dot(mix(cols.xy, cols.yz, offset.x), vec2(0.25));
#      endif
#     endif
#    else
    f = step(shadowmaptc.z, texture2D(Texture_ShadowMap2D, shadowmaptc.xy*ShadowMap_TextureScale).r);
#    endif
#  endif
    return f;
}
# endif

# ifdef USESHADOWMAPCUBE
float ShadowMapCompare(vec3 dir)
{
    // apply depth texture cubemap as light filter
    vec4 shadowmaptc = GetShadowMapTCCube(dir);
    float f;
#  ifdef USESHADOWSAMPLER
    f = shadowCube(Texture_ShadowMapCube, shadowmaptc).r;
#  else
    f = step(shadowmaptc.w, textureCube(Texture_ShadowMapCube, shadowmaptc.xyz).r);
#  endif
    return f;
}
# endif
#endif

#ifdef MODE_WATER

// water pass
void main(void)
{
#ifdef USEOFFSETMAPPING
	// apply offsetmapping
	vec2 TexCoordOffset = OffsetMapping(TexCoord);
#define TexCoord TexCoordOffset
#endif

	vec4 ScreenScaleRefractReflectIW = ScreenScaleRefractReflect * (1.0 / ModelViewProjectionPosition.w);
	//vec4 ScreenTexCoord = (ModelViewProjectionPosition.xyxy + normalize(myhalf3(texture2D(Texture_Normal, TexCoord)) - myhalf3(0.5)).xyxy * DistortScaleRefractReflect * 100) * ScreenScaleRefractReflectIW + ScreenCenterRefractReflect;
	vec4 SafeScreenTexCoord = ModelViewProjectionPosition.xyxy * ScreenScaleRefractReflectIW + ScreenCenterRefractReflect;
	vec4 ScreenTexCoord = SafeScreenTexCoord + vec2(normalize(myhalf3(texture2D(Texture_Normal, TexCoord)) - myhalf3(0.5))).xyxy * DistortScaleRefractReflect;
	// FIXME temporary hack to detect the case that the reflection
	// gets blackened at edges due to leaving the area that contains actual
	// content.
	// Remove this 'ack once we have a better way to stop this thing from
	// 'appening.
	float f = min(1.0, length(texture2D(Texture_Refraction, ScreenTexCoord.xy + vec2(0.01, 0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Refraction, ScreenTexCoord.xy + vec2(0.01, -0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Refraction, ScreenTexCoord.xy + vec2(-0.01, 0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Refraction, ScreenTexCoord.xy + vec2(-0.01, -0.01)).rgb) / 0.05);
	ScreenTexCoord.xy = mix(SafeScreenTexCoord.xy, ScreenTexCoord.xy, f);
	f       = min(1.0, length(texture2D(Texture_Reflection, ScreenTexCoord.zw + vec2(0.01, 0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Reflection, ScreenTexCoord.zw + vec2(0.01, -0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Reflection, ScreenTexCoord.zw + vec2(-0.01, 0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Reflection, ScreenTexCoord.zw + vec2(-0.01, -0.01)).rgb) / 0.05);
	ScreenTexCoord.zw = mix(SafeScreenTexCoord.zw, ScreenTexCoord.zw, f);
	float Fresnel = pow(min(1.0, 1.0 - float(normalize(EyeVector).z)), 2.0) * ReflectFactor + ReflectOffset;
	gl_FragColor = mix(texture2D(Texture_Refraction, ScreenTexCoord.xy) * RefractColor, texture2D(Texture_Reflection, ScreenTexCoord.zw) * ReflectColor, Fresnel);
}

#else // !MODE_WATER
#ifdef MODE_REFRACTION

// refraction pass
void main(void)
{
#ifdef USEOFFSETMAPPING
	// apply offsetmapping
	vec2 TexCoordOffset = OffsetMapping(TexCoord);
#define TexCoord TexCoordOffset
#endif

	vec2 ScreenScaleRefractReflectIW = ScreenScaleRefractReflect.xy * (1.0 / ModelViewProjectionPosition.w);
	//vec2 ScreenTexCoord = (ModelViewProjectionPosition.xy + normalize(myhalf3(texture2D(Texture_Normal, TexCoord)) - myhalf3(0.5)).xy * DistortScaleRefractReflect.xy * 100) * ScreenScaleRefractReflectIW + ScreenCenterRefractReflect.xy;
	vec2 SafeScreenTexCoord = ModelViewProjectionPosition.xy * ScreenScaleRefractReflectIW + ScreenCenterRefractReflect.xy;
	vec2 ScreenTexCoord = SafeScreenTexCoord + vec2(normalize(myhalf3(texture2D(Texture_Normal, TexCoord)) - myhalf3(0.5))).xy * DistortScaleRefractReflect.xy;
	// FIXME temporary hack to detect the case that the reflection
	// gets blackened at edges due to leaving the area that contains actual
	// content.
	// Remove this 'ack once we have a better way to stop this thing from
	// 'appening.
	float f = min(1.0, length(texture2D(Texture_Refraction, ScreenTexCoord + vec2(0.01, 0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Refraction, ScreenTexCoord + vec2(0.01, -0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Refraction, ScreenTexCoord + vec2(-0.01, 0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Refraction, ScreenTexCoord + vec2(-0.01, -0.01)).rgb) / 0.05);
	ScreenTexCoord = mix(SafeScreenTexCoord, ScreenTexCoord, f);
	gl_FragColor = texture2D(Texture_Refraction, ScreenTexCoord) * RefractColor;
}

#else // !MODE_REFRACTION
void main(void)
{
#ifdef USEOFFSETMAPPING
	// apply offsetmapping
	vec2 TexCoordOffset = OffsetMapping(TexCoord);
#define TexCoord TexCoordOffset
#endif

	// combine the diffuse textures (base, pants, shirt)
	myhalf4 color = myhalf4(texture2D(Texture_Color, TexCoord));
#ifdef USECOLORMAPPING
	color.rgb += myhalf3(texture2D(Texture_Pants, TexCoord)) * Color_Pants + myhalf3(texture2D(Texture_Shirt, TexCoord)) * Color_Shirt;
#endif
#ifdef USEVERTEXTEXTUREBLEND
	myhalf terrainblend = clamp(myhalf(gl_Color.a) * color.a * 2.0 - 0.5, myhalf(0.0), myhalf(1.0));
	//myhalf terrainblend = min(myhalf(gl_Color.a) * color.a * 2.0, myhalf(1.0));
	//myhalf terrainblend = myhalf(gl_Color.a) * color.a > 0.5;
	color.rgb = mix(myhalf3(texture2D(Texture_SecondaryColor, TexCoord2)), color.rgb, terrainblend);
	color.a = 1.0;
	//color = mix(myhalf4(1, 0, 0, 1), color, terrainblend);
#endif

#ifdef USEDIFFUSE
	// get the surface normal and the gloss color
# ifdef USEVERTEXTEXTUREBLEND
	myhalf3 surfacenormal = normalize(mix(myhalf3(texture2D(Texture_SecondaryNormal, TexCoord2)), myhalf3(texture2D(Texture_Normal, TexCoord)), terrainblend) - myhalf3(0.5, 0.5, 0.5));
#  ifdef USESPECULAR
	myhalf3 glosscolor = mix(myhalf3(texture2D(Texture_SecondaryGloss, TexCoord2)), myhalf3(texture2D(Texture_Gloss, TexCoord)), terrainblend);
#  endif
# else
	myhalf3 surfacenormal = normalize(myhalf3(texture2D(Texture_Normal, TexCoord)) - myhalf3(0.5, 0.5, 0.5));
#  ifdef USESPECULAR
	myhalf3 glosscolor = myhalf3(texture2D(Texture_Gloss, TexCoord));
#  endif
# endif
#endif



#ifdef MODE_LIGHTSOURCE
	// light source

	// calculate surface normal, light normal, and specular normal
	// compute color intensity for the two textures (colormap and glossmap)
	// scale by light color and attenuation as efficiently as possible
	// (do as much scalar math as possible rather than vector math)
# ifdef USEDIFFUSE
	// get the light normal
	myhalf3 diffusenormal = myhalf3(normalize(LightVector));
# endif
# ifdef USESPECULAR
#  ifndef USEEXACTSPECULARMATH
	myhalf3 specularnormal = normalize(diffusenormal + myhalf3(normalize(EyeVector)));

#  endif
	// calculate directional shading
#  ifdef USEEXACTSPECULARMATH
	color.rgb = myhalf(texture2D(Texture_Attenuation, vec2(length(CubeVector), 0.0))) * (color.rgb * (AmbientScale + DiffuseScale * myhalf(max(float(dot(surfacenormal, diffusenormal)), 0.0))) + (SpecularScale * pow(myhalf(max(float(dot(reflect(diffusenormal, surfacenormal), normalize(EyeVector)))*-1.0, 0.0)), SpecularPower)) * glosscolor);
#  else
	color.rgb = myhalf(texture2D(Texture_Attenuation, vec2(length(CubeVector), 0.0))) * (color.rgb * (AmbientScale + DiffuseScale * myhalf(max(float(dot(surfacenormal, diffusenormal)), 0.0))) + (SpecularScale * pow(myhalf(max(float(dot(surfacenormal, specularnormal)), 0.0)), SpecularPower)) * glosscolor);
#  endif
# else
#  ifdef USEDIFFUSE
	// calculate directional shading
	color.rgb = color.rgb * (myhalf(texture2D(Texture_Attenuation, vec2(length(CubeVector), 0.0))) * (AmbientScale + DiffuseScale * myhalf(max(float(dot(surfacenormal, diffusenormal)), 0.0))));
#  else
	// calculate directionless shading
	color.rgb = color.rgb * myhalf(texture2D(Texture_Attenuation, vec2(length(CubeVector), 0.0)));
#  endif
# endif

#if defined(USESHADOWMAPRECT) || defined(USESHADOWMAPCUBE) || defined(USESHADOWMAP2D)
#if !showshadowmap
    color.rgb *= ShadowMapCompare(CubeVector);
#endif
#endif

# ifdef USECUBEFILTER
	// apply light cubemap filter
	//color.rgb *= normalize(CubeVector) * 0.5 + 0.5;//vec3(textureCube(Texture_Cube, CubeVector));
	color.rgb *= myhalf3(textureCube(Texture_Cube, CubeVector));
# endif
#endif // MODE_LIGHTSOURCE




#ifdef MODE_LIGHTDIRECTION
	// directional model lighting
# ifdef USEDIFFUSE
	// get the light normal
	myhalf3 diffusenormal = myhalf3(normalize(LightVector));
# endif
# ifdef USESPECULAR
	// calculate directional shading
	color.rgb *= AmbientColor + DiffuseColor * myhalf(max(float(dot(surfacenormal, diffusenormal)), 0.0));
#  ifdef USEEXACTSPECULARMATH
	color.rgb += myhalf3(texture2D(Texture_Gloss, TexCoord)) * SpecularColor * pow(myhalf(max(float(dot(reflect(diffusenormal, surfacenormal), normalize(EyeVector)))*-1.0, 0.0)), SpecularPower);
#  else
	myhalf3 specularnormal = normalize(diffusenormal + myhalf3(normalize(EyeVector)));
	color.rgb += myhalf3(texture2D(Texture_Gloss, TexCoord)) * SpecularColor * pow(myhalf(max(float(dot(surfacenormal, specularnormal)), 0.0)), SpecularPower);
#  endif
# else
#  ifdef USEDIFFUSE

	// calculate directional shading
	color.rgb *= AmbientColor + DiffuseColor * myhalf(max(float(dot(surfacenormal, diffusenormal)), 0.0));
#  else
	color.rgb *= AmbientColor;
#  endif
# endif
#endif // MODE_LIGHTDIRECTION




#ifdef MODE_LIGHTDIRECTIONMAP_MODELSPACE
	// deluxemap lightmapping using light vectors in modelspace (evil q3map2)

	// get the light normal
	myhalf3 diffusenormal_modelspace = myhalf3(texture2D(Texture_Deluxemap, TexCoordLightmap)) * 2.0 + myhalf3(-1.0, -1.0, -1.0);
	myhalf3 diffusenormal;
	diffusenormal.x = dot(diffusenormal_modelspace, myhalf3(VectorS));
	diffusenormal.y = dot(diffusenormal_modelspace, myhalf3(VectorT));
	diffusenormal.z = dot(diffusenormal_modelspace, myhalf3(VectorR));
	// calculate directional shading (and undoing the existing angle attenuation on the lightmap by the division)
	// note that q3map2 is too stupid to calculate proper surface normals when q3map_nonplanar
	// is used (the lightmap and deluxemap coords correspond to virtually random coordinates
	// on that luxel, and NOT to its center, because recursive triangle subdivision is used
	// to map the luxels to coordinates on the draw surfaces), which also causes
	// deluxemaps to be wrong because light contributions from the wrong side of the surface
	// are added up. To prevent divisions by zero or strong exaggerations, a max()
	// nudge is done here at expense of some additional fps. This is ONLY needed for
	// deluxemaps, tangentspace deluxemap avoid this problem by design.
	myhalf3 tempcolor = color.rgb * (DiffuseScale * myhalf(max(float(dot(surfacenormal, diffusenormal) / max(0.25, diffusenormal.z)), 0.0)));
		// 0.25 supports up to 75.5 degrees normal/deluxe angle
# ifdef USESPECULAR
#  ifdef USEEXACTSPECULARMATH
	tempcolor += myhalf3(texture2D(Texture_Gloss, TexCoord)) * SpecularScale * pow(myhalf(max(float(dot(reflect(normalize(diffusenormal), surfacenormal), normalize(EyeVector)))*-1.0, 0.0)), SpecularPower);
#  else
	myhalf3 specularnormal = myhalf3(normalize(diffusenormal + myhalf3(normalize(EyeVector))));
	tempcolor += myhalf3(texture2D(Texture_Gloss, TexCoord)) * SpecularScale * pow(myhalf(max(float(dot(surfacenormal, specularnormal)), 0.0)), SpecularPower);
#  endif
# endif

	// apply lightmap color
	color.rgb = color.rgb * AmbientScale + tempcolor * myhalf3(texture2D(Texture_Lightmap, TexCoordLightmap));
#endif // MODE_LIGHTDIRECTIONMAP_MODELSPACE




#ifdef MODE_LIGHTDIRECTIONMAP_TANGENTSPACE
	// deluxemap lightmapping using light vectors in tangentspace (hmap2 -light)

	// get the light normal
	myhalf3 diffusenormal = myhalf3(texture2D(Texture_Deluxemap, TexCoordLightmap)) * 2.0 + myhalf3(-1.0, -1.0, -1.0);
	// calculate directional shading (and undoing the existing angle attenuation on the lightmap by the division)
	myhalf3 tempcolor = color.rgb * (DiffuseScale * myhalf(max(float(dot(surfacenormal, diffusenormal) / diffusenormal.z), 0.0)));
# ifdef USESPECULAR
#  ifdef USEEXACTSPECULARMATH
	tempcolor += myhalf3(texture2D(Texture_Gloss, TexCoord)) * SpecularScale * pow(myhalf(max(float(dot(reflect(diffusenormal, surfacenormal), normalize(EyeVector)))*-1.0, 0.0)), SpecularPower);
#  else
	myhalf3 specularnormal = myhalf3(normalize(diffusenormal + myhalf3(normalize(EyeVector))));
	tempcolor += myhalf3(texture2D(Texture_Gloss, TexCoord)) * SpecularScale * pow(myhalf(max(float(dot(surfacenormal, specularnormal)), 0.0)), SpecularPower);
#  endif
# endif

	// apply lightmap color
	color.rgb = color.rgb * AmbientScale + tempcolor * myhalf3(texture2D(Texture_Lightmap, TexCoordLightmap));
#endif // MODE_LIGHTDIRECTIONMAP_TANGENTSPACE




#ifdef MODE_LIGHTMAP
	// apply lightmap color
	color.rgb = color.rgb * myhalf3(texture2D(Texture_Lightmap, TexCoordLightmap)) * DiffuseScale + color.rgb * AmbientScale;
#endif // MODE_LIGHTMAP




#ifdef MODE_VERTEXCOLOR
	// apply lightmap color
	color.rgb = color.rgb * myhalf3(gl_Color.rgb) * DiffuseScale + color.rgb * AmbientScale;
#endif // MODE_VERTEXCOLOR




#ifdef MODE_FLATCOLOR
#endif // MODE_FLATCOLOR







	color *= TintColor;

#ifdef USEGLOW
#ifdef USEVERTEXTEXTUREBLEND
	color.rgb += mix(myhalf3(texture2D(Texture_SecondaryGlow, TexCoord2)), myhalf3(texture2D(Texture_Glow, TexCoord)), terrainblend);
#else
	color.rgb += myhalf3(texture2D(Texture_Glow, TexCoord)) * GlowScale;
#endif
#endif

	color.rgb *= SceneBrightness;

	// apply fog after Contrastboost/SceneBrightness because its color is already modified appropriately
#ifdef USEFOG
	color.rgb = mix(FogColor, color.rgb, myhalf(texture2D(Texture_FogMask, myhalf2(length(EyeVectorModelSpace)*FogRangeRecip, 0.0))));
#endif

	// reflection must come last because it already contains exactly the correct fog (the reflection render preserves camera distance from the plane, it only flips the side) and ContrastBoost/SceneBrightness
#ifdef USEREFLECTION
	vec4 ScreenScaleRefractReflectIW = ScreenScaleRefractReflect * (1.0 / ModelViewProjectionPosition.w);
	//vec4 ScreenTexCoord = (ModelViewProjectionPosition.xyxy + normalize(myhalf3(texture2D(Texture_Normal, TexCoord)) - myhalf3(0.5)).xyxy * DistortScaleRefractReflect * 100) * ScreenScaleRefractReflectIW + ScreenCenterRefractReflect;
	vec2 SafeScreenTexCoord = ModelViewProjectionPosition.xy * ScreenScaleRefractReflectIW.zw + ScreenCenterRefractReflect.zw;
	vec2 ScreenTexCoord = SafeScreenTexCoord + vec3(normalize(myhalf3(texture2D(Texture_Normal, TexCoord)) - myhalf3(0.5))).xy * DistortScaleRefractReflect.zw;
	// FIXME temporary hack to detect the case that the reflection
	// gets blackened at edges due to leaving the area that contains actual
	// content.
	// Remove this 'ack once we have a better way to stop this thing from
	// 'appening.
	float f = min(1.0, length(texture2D(Texture_Reflection, ScreenTexCoord + vec2(0.01, 0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Reflection, ScreenTexCoord + vec2(0.01, -0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Reflection, ScreenTexCoord + vec2(-0.01, 0.01)).rgb) / 0.05);
	f      *= min(1.0, length(texture2D(Texture_Reflection, ScreenTexCoord + vec2(-0.01, -0.01)).rgb) / 0.05);
	ScreenTexCoord = mix(SafeScreenTexCoord, ScreenTexCoord, f);
	color.rgb = mix(color.rgb, myhalf3(texture2D(Texture_Reflection, ScreenTexCoord)) * ReflectColor.rgb, ReflectColor.a);
#endif

	gl_FragColor = vec4(color);

#if showshadowmap
# ifdef USESHADOWMAPRECT
#  ifdef USESHADOWSAMPLER
	gl_FragColor = shadow2DRect(Texture_ShadowMapRect, GetShadowMapTC2D(CubeVector).xyz);
#  else
	gl_FragColor = texture2DRect(Texture_ShadowMapRect, GetShadowMapTC2D(CubeVector).xy);
#  endif
# endif
# ifdef USESHADOWMAP2D
#  ifdef USESHADOWSAMPLER
    gl_FragColor = shadow2D(Texture_ShadowMap2D, GetShadowMapTC2D(CubeVector).xyz);
#  else
    gl_FragColor = texture2D(Texture_ShadowMap2D, GetShadowMapTC2D(CubeVector).xy);
#  endif
# endif

# ifdef USESHADOWMAPCUBE
#  ifdef USESHADOWSAMPLER
    gl_FragColor = shadowCube(Texture_ShadowMapCube, GetShadowMapTCCube(CubeVector));
#  else
    gl_FragColor = textureCube(Texture_ShadowMapCube, GetShadowMapTCCube(CubeVector).xyz);
#  endif
# endif
#endif
}
#endif // !MODE_REFRACTION
#endif // !MODE_WATER

#endif // FRAGMENT_SHADER

#endif // !MODE_GENERIC
#endif // !MODE_POSTPROCESS
#endif // !MODE_SHOWDEPTH
#endif // !MODE_DEPTH_OR_SHADOW

