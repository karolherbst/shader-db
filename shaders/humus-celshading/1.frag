#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 14


uniform sampler1D CelShade;

varying vec3 lVec;
varying vec3 norm;

void main(){
	vec3 lightVec = normalize(lVec);
	float diffuse = dot(lightVec, norm);

	gl_FragColor = texture1D(CelShade, diffuse);
}

