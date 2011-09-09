#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#define COUNT 40
#define FIRST_PASS
#line 2
uniform mat4 mvp;

uniform vec3 lightPos;
uniform vec3 camPos;

attribute vec2 textureCoord;
attribute vec3 tangent;
attribute vec3 binormal;
attribute vec3 normal;

varying vec2 texCoord;
varying vec3 lVec;
varying vec3 vVec;

varying vec3 dir;

varying vec3 fogCrd;
varying vec3 shadowCrd;


uniform vec4 fogScaleBias;
uniform vec3 shadowScale, shadowBias;

void main(){
	gl_Position = mvp * gl_Vertex;

	vec3 viewVec = camPos - gl_Vertex.xyz;

#ifdef FIRST_PASS
	texCoord = textureCoord;

	vec3 lightVec = lightPos - gl_Vertex.xyz;
	lVec.x = dot(lightVec, tangent);
	lVec.y = dot(lightVec, binormal);
	lVec.z = dot(lightVec, normal);

	vVec.x = dot(viewVec, tangent);
	vVec.y = dot(viewVec, binormal);
	vVec.z = dot(viewVec, normal);
#endif

	dir = viewVec / 40.0;

	fogCrd = gl_Vertex.xyz * fogScaleBias.w + fogScaleBias.xyz;
	shadowCrd = gl_Vertex.xyz * shadowScale + shadowBias;
}



