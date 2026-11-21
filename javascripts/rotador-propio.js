/* Oscilador didáctico: los ángulos y la continuidad se calculan; no ejecuta GNU Radio. */
(()=>{'use strict';
const root=document.getElementById('rotador-animation'),$=id=>root.querySelector('#'+id);
const steps=[
 {title:'1. Mezclar es añadir un giro por muestra',code:'incremento = 2*np.pi*frecuencia_mezcla/samp_rate',body:'Aquí elegimos +400 kHz a 2.4 Msps: Δφ = π/3, es decir, 60° por muestra. El fasor tiene magnitud uno y sus coordenadas son cos φ y sen φ.',detail:'Este ejemplo usa 60° para que un lote de cuatro muestras no complete una vuelta. El caso de sintonía de +600 kHz utiliza 90°.',from:0,to:180,phase:0,group:0},
 {title:'2. Numerar las muestras del primer lote',code:'indices = np.arange(4)  # [0, 1, 2, 3]\nfases = self.fase + incremento*indices',body:'self.fase comienza en cero. Los cuatro ángulos son 0°, 60°, 120° y 180°. Los índices son locales: no indican cuántas muestras procesó antes el bloque.',detail:'El tamaño cuatro es solo un ejemplo; work puede recibir otros tamaños.',from:0,to:180,phase:0,group:0},
 {title:'3. Multiplicar muestra por muestra',code:'oscilador = np.exp(1j*fases)\noutput_items[0][:4] = input_items[0][:4]*oscilador',body:'Con la entrada de prueba x[n]=1+j0, la salida coincide con el oscilador. Cada muestra usa su propio ángulo; no multiplicamos todo el lote por un único complejo fijo.',detail:'Para una entrada general, la multiplicación gira cada muestra y conserva su magnitud.',from:0,to:180,phase:0,group:0},
 {title:'4. Guardar la fase de la próxima muestra',code:'self.fase = (0 + 4*60°) % 360°  # 240°\nreturn 4',body:'La última muestra se multiplicó con 180°, pero la siguiente corresponde a 240°. Se guarda el ángulo del índice N, no el del índice N−1. Los grados facilitan la lectura; el código Python usa radianes.',detail:'En el bloque real: self.fase = (self.fase + incremento*n) % (2*np.pi).',from:180,to:240,phase:240,group:-1},
 {title:'5. Continuar en la segunda llamada',code:'indices = [0, 1, 2, 3]\nfases = 240° + 60°*indices',body:'Los índices locales vuelven a cero, pero la fase inicial sigue en 240°. El segundo lote utiliza 240°, 300°, 360° y 420°: sigue siendo un avance de 60° entre muestras.',detail:'La frontera entre buffers no es una frontera de la señal.',from:240,to:420,phase:240,group:1},
 {title:'6. Comparar con un reinicio incorrecto',code:'# Incorrecto: olvidar self.fase\nfases = incremento*indices',body:'Si se olvida la fase guardada, el segundo lote usa 0°, 60°, 120° y 180°. La muestra global 4 debería usar 240°, pero usa 0°: aparece una discontinuidad en el giro previsto.',detail:'Azul: dirección correcta de la primera muestra del segundo lote. Rojo: dirección con reinicio.',from:240,to:240,phase:240,group:1,wrong:true},
 {title:'7. El módulo no cambia el punto complejo',code:'420° % 360° = 60°\nexp(j*420°) = exp(j*60°)',body:'La última muestra del segundo lote usa 420°, equivalente a 60°. Retirar una vuelta completa no altera el coseno, el seno ni el fasor. Es la misma dirección.',detail:'Esta equivalencia describe una muestra; la fase que debe guardarse corresponde a la siguiente.',from:360,to:420,phase:240,group:1,equivalent:true},
 {title:'8. Guardar 480° como 120°',code:'self.fase = (240° + 4*60°) % 360°\n# 480° % 360° = 120°',body:'Después de las cuatro muestras del segundo lote, la fase de continuación es 480°. La guardamos como 120°, en vez de acumular vueltas indefinidamente. No la ponemos a cero.',detail:'La próxima muestra inicia el tercer lote en 120°, no en 60° ni en 0°.',from:420,to:480,phase:120,group:-1},
 {title:'9. Una misma salida con cualquier partición',code:'self.fase = (self.fase + incremento*n) % (2*np.pi)\nreturn n',body:'Un lote de ocho muestras y dos lotes de cuatro deben generar la misma secuencia de oscilador. Conservar self.fase hace independiente el resultado de la división del trabajo.',detail:'Con frecuencia negativa el módulo conserva una fase equivalente: −60° y 300° apuntan al mismo punto.',from:480,to:660,phase:120,group:-1}
];
let stage=0,playing=false,elapsed=0,start=0,raf=0,last=0;
const duration=10500,reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const fmt=v=>Number(v).toFixed(Math.abs(v-Math.round(v))<1e-8?0:1);
function text(x,y,s,anchor='middle'){return `<text x="${x}" y="${y}" text-anchor="${anchor}">${s}</text>`;}
function spoke(cx,cy,r,deg,color,dash=''){const a=deg*Math.PI/180,x=cx+r*Math.cos(a),y=cy-r*Math.sin(a);return `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="${color}" stroke-width="3" ${dash?'stroke-dasharray="5 4"':''}/><circle cx="${x}" cy="${y}" r="6" fill="${color}"/>`;}
function draw(t=1){const s=steps[stage],w=Math.max(280,Math.floor($('visual').clientWidth)),h=295,cx=w/2,cy=128,r=79;
 const u=playing&&!reduced?t:1;let local=s.wrong?0:(s.group>=0?Math.min(3,Math.floor(u*4)):0);let angle=s.group>=0&&!s.equivalent&&!s.wrong?s.from+60*local:s.from+(s.to-s.from)*u;
 let val=(angle%360+360)%360;
 let svg=`<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--line)"/><line x1="${cx-r-25}" y1="${cy}" x2="${cx+r+25}" y2="${cy}" stroke="var(--line)"/><line x1="${cx}" y1="${cy-r-25}" x2="${cx}" y2="${cy+r+25}" stroke="var(--line)"/>`;
 svg+=text(cx+r+30,cy+5,'I')+text(cx,cy-r-30,'Q');
 svg+=spoke(cx,cy,r,angle,'var(--one)');if(s.wrong)svg+=spoke(cx,cy,r,0,'var(--bad)',true);
 svg+=text(cx,253,s.wrong?'Correcta: 240° · reinicio: 0°':`Ángulo: ${fmt(angle)}° · equivalente: ${fmt(val)}°`);
 svg+=text(cx,280,s.wrong?'El giro entre buffers deja de ser uniforme.':`p = ${Math.cos(angle*Math.PI/180).toFixed(3)} + j · (${Math.sin(angle*Math.PI/180).toFixed(3)})`);
 $('visual').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${s.wrong?'Comparación entre fasor correcto de 240 grados y reinicio de cero grados':'Fasor sobre el círculo unitario y ángulo equivalente'}"><title>Fase del oscilador complejo</title>${svg}</svg>`;
 for(let group=0;group<2;group++){
  $(group===0?'batch-one':'batch-two').innerHTML=Array.from({length:4},(_,i)=>{const a=group*240+i*60,show=s.wrong&&group===1?i*60:a;const active=s.group===group&&(s.equivalent?i===3:i===local);return `<div class="rot-cell ${active?'active':''} ${s.wrong&&group===1?'wrong':''}">${show}°<small>índice local ${i}</small></div>`;}).join('');
 }
}
function render(){const s=steps[stage];$('stage-title').textContent=s.title;$('code').textContent=s.code;$('explain').textContent=s.body;$('detail').textContent=s.detail;$('state').textContent=`Estado: self.fase = ${s.phase}° (${(s.phase*Math.PI/180).toFixed(3)} rad)`;$('count').textContent=`${stage+1} / ${steps.length}`;$('prev').disabled=stage===0;$('next').disabled=stage===steps.length-1;draw();}
function pause(){playing=false;cancelAnimationFrame(raf);$('play').textContent='Reproducir';}
function tick(now){if(!playing)return;elapsed=now-start;const t=Math.min(1,elapsed/duration);$('progress').style.width=t*100+'%';if(now-last>50){if(!reduced)draw(t);last=now;}if(t===1){if(stage===steps.length-1){pause();draw();return;}stage++;elapsed=0;start=now;render();}raf=requestAnimationFrame(tick);}
$('play').onclick=()=>{if(playing){pause();return;}if(stage===steps.length-1&&elapsed>=duration){stage=0;elapsed=0;render();}playing=true;start=performance.now()-elapsed;$('play').textContent='Pausar';raf=requestAnimationFrame(tick);};
function move(d){pause();stage=Math.max(0,Math.min(steps.length-1,stage+d));elapsed=0;$('progress').style.width='0%';render();}
$('prev').onclick=()=>move(-1);$('next').onclick=()=>move(1);
new ResizeObserver(()=>draw(playing?Math.min(1,elapsed/duration):1)).observe($('visual'));
new ResizeObserver(()=>{if(window.frameElement)window.frameElement.style.height=Math.ceil(root.getBoundingClientRect().height+12)+'px';}).observe(root);
render();
})();
