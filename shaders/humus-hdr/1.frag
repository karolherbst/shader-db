#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix

varying vec2 texCoord, lmCoord;
varying vec3 lightVec;
varying vec3 vVec;


#line 36
uniform sampler2D Base;
uniform sampler2D Bump;
uniform sampler2D LightMap;

uniform vec2 plx;
uniform float gloss;

const vec3 lightColor = vec3(0.12, 0.14, 0.2);

void main(){
	vec3 viewVec = normalize(vVec);

	float height = texture2D(Bump, texCoord).a;
	vec2 plxCoord = texCoord + (height * plx.x + plx.y) * viewVec.xy;

	
	vec3 base = texture2D(Base, plxCoord).rgb;
	vec3 bump = texture2D(Bump, plxCoord).xyz;
	vec3 normal = normalize(bump * 2.0 - 1.0);

	float diffuse = saturate(dot(lightVec, normal));
	float specular = pow(saturate(dot(reflect(-viewVec, normal), lightVec)), 16.0);


	vec4 shadow = texture2D(LightMap, lmCoord);

	gl_FragColor.rgb = lightColor * (shadow.x * (diffuse * base + gloss * specular) + 0.7 * shadow.w * base);
}

