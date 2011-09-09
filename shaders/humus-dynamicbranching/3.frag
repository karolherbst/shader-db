#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 13
uniform sampler2D Base;

varying vec2 texCoord;

void main(){
	gl_FragColor = texture2D(Base, texCoord) * gl_Color;
}

