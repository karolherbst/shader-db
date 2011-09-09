#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#define SHADOW_SOFTNESS 0.0005
#define SPHERE_COUNT 7
#line 26


varying vec3 lightVec;
varying vec4 sphereVec[SPHERE_COUNT];

void main(){
	vec4 shadow = vec4(1.0);

	vec3 lVec = lightVec / dot(lightVec, lightVec);
	for (int i = 0; i < SPHERE_COUNT; i++){
		float t = saturate(dot(sphereVec[i].xyz, lVec));
		vec3 p = t * lightVec - sphereVec[i].xyz;
		float len = dot(p, p);

		shadow.w *= saturate(SHADOW_SOFTNESS * len - sphereVec[i].w);
	}

	gl_FragColor = shadow;
}

