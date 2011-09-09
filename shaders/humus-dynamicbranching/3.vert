#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 2
varying vec2 texCoord;

void main(){
	gl_Position = ftransform();
	texCoord = gl_MultiTexCoord0.xy;
	gl_FrontColor = gl_Color;
}



