---
title: Image edge detection with Fourier techniques
date: 2019-12-20
draft: true
---

<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3.0.0/es5/tex-mml-chtml.js"></script>

When \\(a \ne 0\\), there are two solutions to \\(ax^2 + bx + c = 0\\) and they are
\\[x = {-b \pm \sqrt{b^2-4ac} \over 2a}.\\]


<script id="vs" type="x-shader/x-vertex">#version 300 es
in vec2 a_position;

out vec4 v_color;

void main() {
  gl_Position = vec4(a_position, 0, 1);

  v_color = gl_Position * 0.5 + 0.5;
}
</script>

<script id="fs" type="x-shader/x-fragment">#version 300 es
precision mediump float;

in vec4 v_color;

out vec4 outColor;

void main() {
  outColor = v_color;
}
</script>
<canvas id="c"></canvas>
<script src="/js/twgl.js"></script>
<script>
    const gl = document.getElementById("c").getContext("webgl2");
    const programInfo = twgl.createProgramInfo(gl, ["vs", "fs"]);
    
    const arrays = {
        a_position: [-1, 0,
                     0, 1,
                     0, -1],
    };
    const bufferInfo = twgl.createBufferInfoFromArrays(gl, arrays);
    
    function render(time) {
        twgl.resizeCanvasToDisplaySize(gl.canvas);
        gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
        
        gl.useProgram(programInfo.program);
        twgl.setBuffersAndAttributes(gl, programInfo, bufferInfo);
        twgl.drawBufferInfo(gl, bufferInfo);
        
        requestAnimationFrame(render);
    }
    requestAnimationFrame(render);
</script>


