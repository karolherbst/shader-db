#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 18
varying vec3 lightVec;

void main(){
	gl_FragColor = vec4(length(lightVec) + 0.005);
}

