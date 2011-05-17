#version 120

uniform vec3 light_eye;
varying vec4 shadow_coords;
varying vec3 vertex_eye;
uniform sampler2DShadow shadow_sampler;

void main()
{
	vec3 normal = vec3(0.0, 0.0, 1.0);
	vec4 material_color = vec4(1.0, 0.7, 0.5, 1.0);
	float shadow = shadow2DProj(shadow_sampler, shadow_coords).x;
	vec3 l = normalize(light_eye - vertex_eye);
	vec3 v = normalize(-vertex_eye);
	vec3 h = normalize(l + v);
	float n_dot_l = dot(normal, l);
	vec3 diffuse = material_color.xyz * n_dot_l;
	float specular = pow(dot(normal, h), 16.0);
	gl_FragColor = step(0.0, n_dot_l) *
	vec4((diffuse + vec3(specular)) * shadow, material_color.w);
}
