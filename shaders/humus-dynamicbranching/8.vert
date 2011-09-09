#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 2
uniform vec3 lightPos;
uniform vec3 camPos;
uniform float invRadius;

attribute vec2 textureCoord;
attribute vec3 tangent;
attribute vec3 binormal;
attribute vec3 normal;

varying vec2 texCoord;
varying vec3 lVec;
varying vec3 vVec;
varying vec3 shadowVec;

void main(){
	gl_Position = ftransform();

	texCoord = textureCoord;

	vec3 lightVec = invRadius * (lightPos - gl_Vertex.xyz);
	shadowVec = -lightVec;
	lVec.x = dot(lightVec, tangent);
	lVec.y = dot(lightVec, binormal);
	lVec.z = dot(lightVec, normal);

	vec3 viewVec = camPos - gl_Vertex.xyz;
	vVec.x = dot(viewVec, tangent);
	vVec.y = dot(viewVec, binormal);
	vVec.z = dot(viewVec, normal);
}



