#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec2 texCoord0;
varying vec2 texCoord1;
varying vec2 texCoord2;
varying vec2 texCoord3;


#line 9
uniform vec2 halfPixel;

void main(){
	gl_Position = gl_Vertex;

	vec2 texCoord = gl_Vertex.xy * 0.5 + 0.5;

	texCoord0 = texCoord + halfPixel * vec2( 1,  1);
	texCoord1 = texCoord + halfPixel * vec2(-1,  1);
	texCoord2 = texCoord + halfPixel * vec2(-1, -1);
	texCoord3 = texCoord + halfPixel * vec2( 1, -1);
}



