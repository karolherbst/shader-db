#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec2 texCoord0;
varying vec2 texCoord1;
varying vec2 texCoord2;
varying vec2 texCoord3;


#line 9
uniform vec2 sample0, sample1, sample2, sample3;

void main(){
	gl_Position = gl_Vertex;

	vec2 texCoord = gl_Vertex.xy * 0.5 + 0.5;
	texCoord0 = texCoord + sample0;
	texCoord1 = texCoord + sample1;
	texCoord2 = texCoord + sample2;
	texCoord3 = texCoord + sample3;
}



