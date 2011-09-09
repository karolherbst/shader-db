#version 120
#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 28
uniform sampler2D Base;
uniform sampler2D Bump;

uniform vec2 plxCoeffs;
uniform bool hasParallax;

varying vec2 texCoord;
varying vec3 vVec;

void main(){

#ifdef MULTIPASS
	vec3 viewVec = normalize(vVec);

	vec2 plxTexCoord = texCoord;
	if (hasParallax){
		float height = texture2D(Bump, texCoord).w;
		float offset = height * plxCoeffs.x + plxCoeffs.y;
		plxTexCoord += offset * viewVec.xy;
	}

	vec4 base = texture2D(Base, plxTexCoord);

	gl_FragColor = 0.1 * base;
#endif

}

