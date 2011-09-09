#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec2 texCoord;


#line 6
void main(){
	gl_Position = gl_Vertex;

	texCoord = gl_Vertex.xy * 0.5 + 0.5;
}



