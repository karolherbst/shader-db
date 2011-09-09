#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 2
uniform mat4 mvp;

void main(){
	gl_Position = mvp * gl_Vertex;
}



