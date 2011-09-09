#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 0


uniform vec3 lightPos;

uniform float scale;
uniform vec3 offset;

varying vec3 lightVec;
varying vec3 normal;

void main(){
	vec4 pos = gl_Vertex;
	pos.xyz *= scale;
	pos.xyz += offset;

	gl_Position = gl_ModelViewProjectionMatrix * pos;

	lightVec = normalize(lightPos - pos.xyz);
	normal = gl_Vertex.xyz;
}



