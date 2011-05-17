attribute vec4 att0;
varying vec4 var0;
attribute vec2 att1;
varying vec2 var1;
attribute vec3 att2;
varying vec3 var2;


varying vec3 varposition;
varying vec3 varnormal;

void main()
{
	vec4 co = gl_ModelViewMatrix * gl_Vertex;

	varposition = co.xyz;
	varnormal = gl_NormalMatrix * gl_Normal;
	gl_Position = gl_ProjectionMatrix * co;

	var0 = att0;
	var1 = att1;
	var2 = gl_NormalMatrix * att2;
}


