#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 0


varying vec2 texCoord;
varying vec3 lightVec;
varying vec3 viewVec;

uniform vec3 lightPos;
uniform vec3 camPos;

void main(){
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

	texCoord = gl_MultiTexCoord0.xy;

	vec3 lVec = lightPos - gl_Vertex.xyz;
	lightVec.x = dot(gl_MultiTexCoord1.xyz, lVec);
	lightVec.y = dot(gl_MultiTexCoord2.xyz, lVec);
	lightVec.z = dot(gl_MultiTexCoord3.xyz, lVec);

	vec3 vVec = camPos - gl_Vertex.xyz;
	viewVec.x = dot(gl_MultiTexCoord1.xyz, vVec);
	viewVec.y = dot(gl_MultiTexCoord2.xyz, vVec);
	viewVec.z = dot(gl_MultiTexCoord3.xyz, vVec);
}



