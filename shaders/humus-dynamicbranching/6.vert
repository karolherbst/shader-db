#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#define SHADOWS
#define LIGHT_COUNT 3
#line 2
uniform vec3 camPos;
uniform vec3 lightPos[LIGHT_COUNT];
uniform float invRadius[LIGHT_COUNT];

attribute vec2 textureCoord;
attribute vec3 tangent;
attribute vec3 binormal;
attribute vec3 normal;

varying vec3 lVec[LIGHT_COUNT];
varying vec2 texCoord;
varying vec3 vVec;
#ifdef SHADOWS
varying vec3 shadowVec[LIGHT_COUNT];
#endif

void main(){
	gl_Position = ftransform();

	texCoord = textureCoord;

	for (int i = 0; i < LIGHT_COUNT; i++){
		vec3 lightVec = invRadius[i] * (lightPos[i] - gl_Vertex.xyz);

#ifdef SHADOWS
		shadowVec[i] = -lightVec;
#endif
		lVec[i].x = dot(lightVec, tangent);
		lVec[i].y = dot(lightVec, binormal);
		lVec[i].z = dot(lightVec, normal);
	}

	vec3 viewVec = camPos - gl_Vertex.xyz;
	vVec.x = dot(viewVec, tangent);
	vVec.y = dot(viewVec, binormal);
	vVec.z = dot(viewVec, normal);
}



