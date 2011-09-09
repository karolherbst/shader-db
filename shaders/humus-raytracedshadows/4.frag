#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 25


uniform vec4 color;

varying vec3 lVec;
varying vec3 vVec;
varying vec3 norm;

void main(){
	vec3 lightVec = (lVec);
	vec3 viewVec = (vVec);
	vec3 normal = normalize(norm);

	float diffuse = saturate(dot(lightVec, normal));
	float specular = pow(saturate(dot(reflect(-viewVec, normal), lightVec)), 20.0);

	gl_FragColor = diffuse * color + specular;
}

