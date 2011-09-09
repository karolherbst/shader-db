#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec2 texCoord0;
varying vec2 texCoord1;
varying vec2 texCoord2;
varying vec2 texCoord3;


#line 25
uniform sampler2D Image;

uniform float invRange;

void main(){
	// Downscale and convert to fixed point
	vec3 base = texture2D(Image, texCoord0).rgb;
	base     += texture2D(Image, texCoord1).rgb;
	base     += texture2D(Image, texCoord2).rgb;
	base     += texture2D(Image, texCoord3).rgb;

	// Clamp for nvidia ...
	gl_FragColor.rgb = min(base.rgb * invRange, 1.0);
}

