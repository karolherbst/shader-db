#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#define BATCH_INSTANCES 64
#line 45
uniform sampler3D Noise;

uniform float fade;

varying vec3 texCoord;
varying vec3 normal;
varying vec3 lVec;

void main(){
	vec3 lightVec = normalize(lVec);
	vec3 viewVec = lightVec;

	float atten = saturate(1.0 / (1.0 + dot(lVec, lVec)) - 0.1);

	vec4 darkWood = vec4(0.09, 0.04, 0.01, 1.0);
	vec4 liteWood = vec4(0.92, 0.51, 0.13, 1.0);

	float rings = fract(texture3D(Noise, texCoord * 0.15, 1.0).x * 4.0);
	rings *= 4.0 * (1.0 - rings);
	rings *= rings;

	float n = texture3D(Noise, texCoord).x;

	vec4 base = lerp(darkWood, liteWood, rings + n);

	float diffuse = saturate(dot(lightVec, normal));
	float specular = pow(diffuse, 64.0);

	gl_FragColor = fade * atten * ((diffuse * 0.8 + 0.2) * base + 0.4 * specular);
}

