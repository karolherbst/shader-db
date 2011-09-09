#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 0


uniform vec3 lightPos;
uniform vec3 camPos;

attribute vec2 textureCoord;
attribute vec3 tangent;
attribute vec3 binormal;
attribute vec3 normal;

varying vec2 texCoord;
varying vec3 lVec;

void main(){
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
	texCoord = textureCoord;

	vec3 lightVec = lightPos - gl_Vertex.xyz;
	vec3 viewVec = lightPos - gl_Vertex.xyz;

	lVec.x = dot(lightVec, tangent);
	lVec.y = dot(lightVec, binormal);
	lVec.z = dot(lightVec, normal);
}



