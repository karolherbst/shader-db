#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 2
attribute vec2 textureCoord;
attribute vec3 tangent;
attribute vec3 binormal;
attribute vec3 normal;

uniform vec3 camPos;

varying vec2 texCoord;
varying vec3 vVec;

void main(){
	gl_Position = ftransform();

#ifdef MULTIPASS
	texCoord = textureCoord;

	vec3 viewVec = camPos - gl_Vertex.xyz;
	vVec.x = dot(viewVec, tangent);
	vVec.y = dot(viewVec, binormal);
	vVec.z = dot(viewVec, normal);
#endif
}



