#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec2 texCoord, lmCoord;
varying vec3 lightVec;
varying vec3 vVec;


#line 8
attribute vec2 textureCoord;
attribute vec3 tangent;
attribute vec3 binormal;
attribute vec3 normal;
attribute vec2 lightMapCoord;

uniform vec3 lightDir;
uniform vec3 camPos;

void main(){
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

	texCoord = textureCoord;
	lmCoord = lightMapCoord;

	lightVec.x = dot(lightDir, tangent);
	lightVec.y = dot(lightDir, binormal);
	lightVec.z = dot(lightDir, normal);

	vec3 viewVec = camPos - gl_Vertex.xyz;
	vVec.x = dot(viewVec, tangent);
	vVec.y = dot(viewVec, binormal);
	vVec.z = dot(viewVec, normal);
}



