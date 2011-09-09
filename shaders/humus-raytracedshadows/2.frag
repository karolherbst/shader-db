#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 26


uniform sampler2D Base;
uniform sampler2D Bump;

varying vec2 texCoord;
varying vec3 lVec;

void main(){
	vec4 base = texture2D(Base, texCoord);
	vec3 bump = normalize(texture2D(Bump, texCoord).xyz * 2.0 - 1.0);

	float diffuse = dot(normalize(lVec), bump);

	gl_FragColor = diffuse * base;
}

