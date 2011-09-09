#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#define SHADOW_SOFTNESS 0.0005
#define SPHERE_COUNT 7
#line 0


uniform float scale;
uniform vec3 offset;

uniform vec3 lightPos;
uniform vec4 spherePos[SPHERE_COUNT];

varying vec3 lightVec;
varying vec4 sphereVec[SPHERE_COUNT];

void main(){
	vec4 pos = gl_Vertex;
	pos.xyz *= scale;
	pos.xyz += offset;

	gl_Position = gl_ModelViewProjectionMatrix * pos;

	lightVec = lightPos - pos.xyz;
	for (int i = 0; i < SPHERE_COUNT; i++){
		sphereVec[i].xyz = spherePos[i].xyz - pos.xyz;
		sphereVec[i].w = spherePos[i].w * SHADOW_SOFTNESS - 0.5;
	}
}



