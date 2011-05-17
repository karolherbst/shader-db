uniform sampler2D shadow_sampler;
varying vec2 texcoord;

void main()
{
	gl_FragColor = texture2D(shadow_sampler, texcoord);
}
