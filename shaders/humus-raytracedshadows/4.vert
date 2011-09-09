#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 0


uniform float scale;
uniform vec3 offset;

uniform vec3 lightPos;
uniform vec3 camPos;

varying vec3 lVec;
varying vec3 vVec;
varying vec3 norm;

void main(){
	vec4 pos = gl_Vertex;
	pos.xyz *= scale;
	pos.xyz += offset;

	gl_Position = gl_ModelViewProjectionMatrix * pos;

	lVec = normalize(lightPos - pos.xyz);
	vVec = normalize(camPos - pos.xyz);
	norm = gl_Vertex.xyz;
}



