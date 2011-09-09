#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 0


uniform vec3 lightPos;

varying vec3 lVec;
varying vec3 norm;

void main(){
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

	lVec = lightPos - gl_Vertex.xyz;
	norm = gl_Normal;
}


