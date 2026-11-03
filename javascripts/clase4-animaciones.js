/* Animaciones didácticas de clase 4; valores de ejemplo exactos, sin ejecutar el planificador. */
(()=>{'use strict';
const data=JSON.parse(document.getElementById('lesson-data').textContent),$=id=>document.getElementById(id);
let stage=0,playing=false,elapsed=0,start=0,raf=0,last=0;const duration=9500,reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paramSteps=[
 ['Python entiende la sintaxis','class cu8_a_c64(gr.decim_block):','class y def pertenecen a Python. gr.decim_block aporta la clase base de GNU Radio, que conoce la relación entre elementos de los puertos.','Lenguaje y biblioteca cumplen tareas distintas.'],
 ['GRC recoge la configuración','def __init__(self, escala=127.5):','El argumento con valor predeterminado se declara en el YAML como propiedad del bloque OOT. Al crear el objeto, GRC pasa el valor elegido; aquí será 127.5.','El parámetro no es una muestra del stream.'],
 ['Python inicializa una instancia','conversor = cu8_a_c64(escala=127.5)','Python llama a __init__ sobre la nueva instancia. self se refiere a esa instancia; permite distinguir su configuración de la de otros bloques.','__init__ se ejecuta al crear el bloque, no por cada lote de muestras.'],
 ['GNU Radio configura los puertos','gr.decim_block.__init__(self, name="Conversor", in_sig=[np.uint8], out_sig=[np.complex64], decim=2)','La firma crea un puerto Byte y uno Complex. decim=2 declara que se necesitan dos entradas por cada salida. No se están calculando todavía los valores de la señal.','Una entrada tiene muchos elementos; no se crea un puerto para I y otro para Q.'],
 ['La instancia conserva el parámetro','self.escala = float(escala)','La asignación guarda 127.5 en el atributo escala del objeto. work podrá consultarlo con self.escala; el inicializador de GNU Radio no guarda ese parámetro de usuario automáticamente.','Aquí se conserva la configuración; in_sig y out_sig ya definieron los tipos.'],
 ['El planificador llama a work repetidamente','work(input_items, output_items) → return n','GNU Radio proporciona buffers; work calcula n complejos usando self.escala y escribe la salida. La clase base consume 2n bytes. El siguiente lote usa la misma instancia.','El ritmo de llamada lo organiza GNU Radio; los cálculos están escritos en Python y NumPy.']
];
const convertSteps=[
 ['Leer cuatro bytes del archivo','datos = [255, 0, 0, 255]','Son dos muestras: I₀=255, Q₀=0; I₁=0, Q₁=255. Cada componente llega como uint8.','Dos bytes representan un instante; no cuatro instantes diferentes.'],
 ['Recibir dos posiciones de salida','n = len(output_items[0]); datos = input_items[0][:2*n]','Para n=2 complejos se toman 2n=4 bytes. El planificador conoce esta relación por decim=2.','input_items[0] elige el primer puerto, no el primer byte.'],
 ['Separar posiciones pares e impares','i = datos[0::2]; q = datos[1::2]','Las posiciones 0 y 2 van a I; las posiciones 1 y 3 van a Q. Se conserva qué I pertenece a cada Q.','NumPy selecciona arreglos completos: no necesitamos un bucle por muestra.'],
 ['Convertir antes de restar','i = i.astype(np.float32); q = q.astype(np.float32)','Los valores pasan a flotantes: 255.0 y 0.0. Ahora una resta puede producir números negativos sin el desbordamiento propio de enteros sin signo.','astype cambia el tipo de representación; todavía no cambia la amplitud numérica.'],
 ['Centrar y normalizar cada componente','i = (i - 127.5)/self.escala; q = (q - 127.5)/self.escala','Con escala=127.5: 255 se transforma en +1 y 0 se transforma en −1. La animación desplaza los valores entre ambas representaciones.','Cada componente queda entre −1 y +1; la magnitud del complejo puede llegar a √2.'],
 ['Reunir I y Q por cada instante','output_items[0][:n] = i + 1j*q','Se combinan I₀ con Q₀ e I₁ con Q₁. Python usa 1j para la unidad imaginaria; la salida se almacena como complex64.','Resultado exacto: x₀=1−1j y x₁=−1+1j.'],
 ['Informar cuántos complejos se produjeron','return n  # n = 2','Se devuelven dos elementos producidos. gr.decim_block consume cuatro elementos Byte. La muestra física conserva su tiempo, aunque cambie el tamaño de su representación.','4 bytes de entrada → 2 complejos de 8 bytes = 16 bytes de salida.']
];
const steps=data.kind==='python'?paramSteps:convertSteps;
function text(x,y,s,anchor='middle',color='var(--fg)'){return `<text x="${x}" y="${y}" text-anchor="${anchor}" style="fill:${color}">${esc(s)}</text>`;}
function rect(x,y,w,h,fill='var(--muted)'){return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6" fill="${fill}"/>`;}
function renderPython(t){const active=stage<1?0:stage<3?1:stage===3?2:stage===4?3:4;const nodes=[['Python','class · def · __init__ · self'],['Configuración de GRC','escala = 127.5'],['Infraestructura GNU Radio','uint8 → complex64 · decim = 2'],['Estado de la instancia','self.escala = 127.5'],['Procesamiento del stream','2n bytes → work → n complejos']];
$('visual').innerHTML='<div class="flow">'+nodes.map(([a,b],i)=>`<div class="node ${i===active?'active':''}"><strong>${esc(a)}</strong><span>${esc(b)}</span>${i===4&&stage===5?`<div class="lesson-lots"><span style="transform:translateX(${playing?t*45:45}%)">Lote de bytes → work → complejos</span></div>`:''}</div>`).join('')+'</div>';}
function positions(s,w){let a=[];for(let k=0;k<4;k++){if(s<2)a.push({x:w*(.125+.25*k),y:80});else if(s<5)a.push({x:w*(k<2?.3:.7),y:k%2===0?105:190});else a.push({x:w*(k<2?.25:.75),y:k%2===0?95:165});}return a;}
function renderConversion(t){const w=Math.max(280,Math.floor($('visual').clientWidth)),h=310,target=positions(stage,w),from=positions(Math.max(0,stage-1),w),u=playing&&!reduced?t:1;let out=text(w/2,24,stage<2?'Byte stream · puerto 0':stage<5?'Dos arreglos: I y Q':'Buffer de salida · puerto 0');
if(stage>=5){out+=rect(8,48,w/2-16,170)+rect(w/2+8,48,w/2-16,170);out+=text(w*.25,244,'x₀ = 1 − 1j')+text(w*.75,244,'x₁ = −1 + 1j');}
else if(stage>=2)out+=text(12,109,'I','start')+text(12,194,'Q','start');
const labels=['I₀','Q₀','I₁','Q₁'],raw=[255,0,0,255];for(let k=0;k<4;k++){let pos={x:from[k].x+(target[k].x-from[k].x)*u,y:from[k].y+(target[k].y-from[k].y)*u};let value=raw[k];if(stage===4){value=raw[k]+((raw[k]-127.5)/127.5-raw[k])*u;}else if(stage>=5)value=(raw[k]-127.5)/127.5;let shown=stage===4&&u<1?value.toFixed(1):stage>=4?(value>0?'+':'')+value.toFixed(0):stage===3?value.toFixed(1):String(value);out+=rect(pos.x-30,pos.y-25,60,60,k%2===0?'color-mix(in srgb,var(--one) 22%,var(--bg))':'color-mix(in srgb,var(--two) 22%,var(--bg))')+text(pos.x,pos.y-5,labels[k])+text(pos.x,pos.y+20,shown);}
out+=text(w/2,285,stage===6?'Producir 2 · consumir 4 · sin perder parejas I/Q':stage<2?'[255, 0, 0, 255] → dos muestras físicas':stage<5?'I y Q se mantienen asociadas por índice':'complex64 = float32 real + float32 imaginario');$('visual').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(steps[stage][0])}"><title>${esc(steps[stage][0])}</title>${out}</svg>`;}
function draw(t=1){if(data.kind==='python')renderPython(t);else renderConversion(t);}
function render(){const s=steps[stage];$('stage-title').textContent=s[0];$('code').textContent=s[1];$('explain').textContent=s[2];$('detail').textContent=s[3];$('count').textContent=`${stage+1} / ${steps.length}`;$('prev').disabled=stage===0;$('next').disabled=stage===steps.length-1;draw();}
function pause(){playing=false;cancelAnimationFrame(raf);$('play').textContent='Reproducir';}
function tick(now){if(!playing)return;elapsed=now-start;const t=Math.min(1,elapsed/duration);$('progress').style.width=t*100+'%';if(now-last>50){if(!reduced)draw(t);last=now;}if(t===1){if(stage===steps.length-1){pause();draw();return;}stage++;start=now;elapsed=0;render();}raf=requestAnimationFrame(tick);}
$('play').onclick=()=>{if(playing){pause();return;}if(stage===steps.length-1&&elapsed>=duration){stage=0;elapsed=0;render();}playing=true;start=performance.now()-elapsed;$('play').textContent='Pausar';raf=requestAnimationFrame(tick);};
function move(d){pause();stage=Math.max(0,Math.min(steps.length-1,stage+d));elapsed=0;$('progress').style.width='0%';render();}
$('prev').onclick=()=>move(-1);$('next').onclick=()=>move(1);
new ResizeObserver(()=>draw(playing?Math.min(1,elapsed/duration):1)).observe($('visual'));
new ResizeObserver(()=>{if(window.frameElement)window.frameElement.style.height=(Math.ceil($('clase4-animation').getBoundingClientRect().height)+12)+'px';}).observe($('clase4-animation'));render();
})();
