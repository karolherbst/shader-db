#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#define COUNT 40
#define FIRST_PASS
#line 52
uniform sampler2D Base;
uniform sampler2D Bump;
uniform sampler3D Fog;
uniform sampler3D LightMap;

varying vec2 texCoord;
varying vec3 lVec;
varying vec3 vVec;

varying vec3 dir;

varying vec3 fogCrd;
varying vec3 shadowCrd;

uniform float fogStart;
uniform vec3 shadowStart;

uniform vec4 fogScaleBias;
uniform vec3 shadowScale, shadowBias;

void main(){
	const vec3 fogColor = vec3(0.9, 1.0, 0.8);
	const float fogDensity = 0.005;

	float n = fogDensity * length(dir);

	vec3 fogCoord = fogCrd;
	vec3 shadowCoord = shadowCrd;

#ifdef FIRST_PASS

	// Regular per pixel lighting
	float atten = 1.0 / (1.0 + 0.000001 * dot(lVec, lVec));
	vec3 lightVec = normalize(lVec);
	vec3 viewVec = normalize(vVec);

	vec3 base = texture2D(Base, texCoord).rgb;
	vec3 normal = normalize(texture2D(Bump, texCoord).xyz * 2.0 - 1.0);

	float diffuse = saturate(dot(lightVec, normal));
	float specular = pow(saturate(dot(reflect(-viewVec, normal), lightVec)), 16.0);

	float shadow = texture3D(LightMap, shadowCrd).x;

	vec3 lighting = atten * shadow * (diffuse * base + 0.5 * specular) + 0.14 * base;
#else

	// For later passes, continue the fog computation where we stopped last pass
	fogCoord += fogStart * dir;
	shadowCoord += shadowStart * dir;

#endif

	float a = 1.0;
	float b = 0.0;

	// Volumetric fog computation
	for (int i = 0; i < COUNT; i++){
		fogCoord += fogScaleBias.w * dir;
		shadowCoord += shadowScale * dir;

		float fog = texture3D(Fog, fogCoord).x;
		float shadow = texture3D(LightMap, shadowCoord).x;

		// Compute weighting factors. This implements the commented out lerp more efficiently.
		float x = 1.0 - fog * n;
		a *= x;
		b = lerp(shadow, b, x);
	}

#ifdef FIRST_PASS
	gl_FragColor.rgb = lighting * a + fogColor * b;
#else
	// "lighting" is in the framebuffer, so we use alpha blending to multiply it with "a".
	gl_FragColor.rgb = b * fogColor;
	gl_FragColor.a = a;
#endif

}

