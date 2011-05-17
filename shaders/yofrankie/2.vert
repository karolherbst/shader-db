attribute vec2 att0;
varying vec2 var0;


varying vec3 varposition;
varying vec3 varnormal;

void main()
{
	vec4 co = gl_ModelViewMatrix * gl_Vertex;

	varposition = co.xyz;
	varnormal = gl_NormalMatrix * gl_Normal;
	gl_Position = gl_ProjectionMatrix * co;

	var0 = att0;
}


