#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec3 cubeCoord;


#line 6
void main(){
	gl_Position = gl_Vertex;
	cubeCoord = gl_MultiTexCoord0.xyz;
}



