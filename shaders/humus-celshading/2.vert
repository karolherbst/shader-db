#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 0


uniform vec3 camPos;
uniform float outlineThreshold;
uniform float edgeThreshold;

varying vec3 norm;

void main(){
	vec4 pos = gl_Vertex;
    vec3 dir = camPos - gl_Vertex.xyz;

	pos.w = float(
		dot(dir, gl_MultiTexCoord0.xyz) * dot(dir, gl_MultiTexCoord1.xyz) < outlineThreshold ||
		dot(gl_MultiTexCoord0.xyz, gl_MultiTexCoord1.xyz) < edgeThreshold);

	gl_Position = gl_ModelViewProjectionMatrix * pos;
}


