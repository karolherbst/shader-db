#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec2 texCoord;


#line 15
uniform sampler2D Base;
uniform sampler2D Blur;

uniform float exposure;
uniform float range;
uniform float blurStrength;

void main(){
	vec4 base = texture2D(Base, texCoord);
	vec4 blur = texture2D(Blur, texCoord);

	blur.rgb = pow(blur.rgb, vec3(blurStrength));

	blur *= range;

	vec4 color = base + blur;

	gl_FragColor.rgb = 1.0 - exp(-exposure * color.rgb);
}

