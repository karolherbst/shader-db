#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#define BATCH_INSTANCES 64
#line 2
uniform vec3 camPos;

void rotate(const vec2 sc, inout vec2 pos){
	pos.xy = vec2(dot(pos, sc), dot(pos, vec2(-sc.y, sc.x)));
}

varying vec3 texCoord;
varying vec3 normal;
varying vec3 lVec;

uniform vec4 attribs[BATCH_INSTANCES];
uniform float time;

uniform float fallAngle;

void main(){
	vec4 attrib = attribs[int(gl_MultiTexCoord0.x)];

	float a = saturate(time - attrib.w);
	a = fallAngle * pow(a, 0.8);

	vec2 scA = vec2(cos(a), sin(a));
	vec2 scB = vec2(cos(-attrib.z), sin(-attrib.z));

	vec4 position = gl_Vertex;
	normal = gl_Normal;
	rotate(scA, position.xy);
	rotate(scA, normal.xy);
	rotate(scB, position.xz);
	rotate(scB, normal.xz);

	position.xz += attrib.xy;

	gl_Position = gl_ModelViewProjectionMatrix * position;

	texCoord = gl_Vertex.xyz * 0.283 + attrib.w * vec3(7.243, 2.6783, 9.4921);

	lVec = 0.005 * (camPos - position.xyz);
}



