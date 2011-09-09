#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec2 texCoord0;
varying vec2 texCoord1;
varying vec2 texCoord2;
varying vec2 texCoord3;


#line 24
uniform sampler2D Image;

void main(){
	vec3 base = texture2D(Image, texCoord0).rgb;
	base     += texture2D(Image, texCoord1).rgb;
	base     += texture2D(Image, texCoord2).rgb;
	base     += texture2D(Image, texCoord3).rgb;

	gl_FragColor.rgb = 0.25 * base.rgb;
}

