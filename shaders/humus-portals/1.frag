#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 26


uniform sampler2D Base;
uniform sampler2D Bump;

uniform float invRadius;
uniform float ambient;

varying vec2 texCoord;
varying vec3 lightVec;
varying vec3 viewVec;

void main(){
	vec4 base = texture2D(Base, texCoord);
	vec3 bump = texture2D(Bump, texCoord).xyz * 2.0 - 1.0;

	bump = normalize(bump);

	float distSqr = dot(lightVec, lightVec);
	vec3 lVec = lightVec * inversesqrt(distSqr);

	float atten = clamp(1.0 - invRadius * sqrt(distSqr), 0.0, 1.0);
	float diffuse = clamp(dot(lVec, bump), 0.0, 1.0);

	float specular = pow(clamp(dot(reflect(normalize(-viewVec), bump), lVec), 0.0, 1.0), 16.0);
	
	gl_FragColor = ambient * base + (diffuse * base + 0.6 * specular) * atten;
}

