#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 22


uniform vec4 color;

varying vec3 lightVec;
varying vec3 normal;

void main(){
	float diffuse = 0.17 * (0.4 * dot(lightVec, normal) + 0.6);

	gl_FragColor = diffuse * color;
}

