#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 2
uniform vec3 camPos;

varying vec2 texCoord;
varying vec3 lVec;

void main(){
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

	texCoord = gl_Vertex.xz * 0.0625;

	lVec = 0.005 * (camPos - gl_Vertex.xyz).xzy;
}



