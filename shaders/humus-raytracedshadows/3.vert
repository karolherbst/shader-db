#define saturate(x) clamp(x,0.0,1.0)
#define lerp mix
#line 0


attribute vec2 textureCoord;

varying vec2 texCoord;

void main(){
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
	texCoord = textureCoord;
}



