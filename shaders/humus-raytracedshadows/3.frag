#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 12


uniform sampler2D Base;

varying vec2 texCoord;

void main(){
	vec4 base = texture2D(Base, texCoord);

	gl_FragColor = 0.17 * base;
}

