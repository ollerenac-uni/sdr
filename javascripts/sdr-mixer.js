/* Vistas coordinadas de una misma secuencia I/Q. */
(function () {
  "use strict";
  if (typeof document === "undefined") return;
  const M = globalThis.SDRMixerModel;
  const NS = "http://www.w3.org/2000/svg";
  const PRESETS = {
    original: { mixHz: 0, phaseDeg: 0, mode: "tone", title: "Sin mezcla: la salida coincide con la entrada." },
    centered: { mixHz: -400000, phaseDeg: 0, mode: "tone", title: "Tono centrado: se cancela el giro de +400 kHz." },
    phase: { mixHz: -400000, phaseDeg: 45, mode: "tone", title: "Misma frecuencia centrada, otra fase: I y Q quedan en 0.707." },
    modulated: { mixHz: -400000, phaseDeg: 0, mode: "fm", title: "Señal FM centrada: la variación de la modulación permanece." }
  };
  let mounted = null;

  function element(tag, attrs = {}, content) {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (content !== undefined) node.textContent = content;
    return node;
  }

  function add(svg, tag, attrs, content) {
    const node = element(tag, attrs, content);
    svg.appendChild(node);
    return node;
  }

  function number(value, digits = 3) {
    const clean = Math.abs(value) < 0.5 * 10 ** -digits ? 0 : value;
    return clean.toFixed(digits);
  }

  function hz(value) {
    return `${value > 0 ? "+" : ""}${number(value / 1000, 0)} kHz`;
  }

  function complex(z) {
    return `${number(z.i)} ${z.q < -0.0005 ? "−" : "+"} j${number(Math.abs(z.q))}`;
  }

  function line(svg, x1, y1, x2, y2, cls) {
    add(svg, "line", { x1, y1, x2, y2, class: cls });
  }

  function label(svg, x, y, content, cls = "sdr-label", anchor = "middle") {
    add(svg, "text", { x, y, class: cls, "text-anchor": anchor }, content);
  }

  function chart(container, title, draw) {
    const panel = document.createElement("div");
    panel.className = "sdr-chart";
    const heading = document.createElement("h4");
    heading.textContent = title;
    const svg = element("svg", { viewBox: "0 0 400 310", role: "img", "aria-label": title });
    add(svg, "title", {}, title);
    draw(svg);
    panel.append(heading, svg);
    container.appendChild(panel);
  }

  function plane(svg, z, output) {
    const ox = 200, oy = 155, scale = 96;
    const px = ox + z.i * scale, py = oy - z.q * scale;
    add(svg, "circle", { cx: ox, cy: oy, r: scale, class: "sdr-circle" });
    line(svg, 57, oy, 343, oy, "sdr-axis");
    line(svg, ox, 26, ox, 282, "sdr-axis");
    label(svg, 348, oy + 6, "I", "sdr-i sdr-axis-name");
    label(svg, ox + 15, 29, "Q", "sdr-q sdr-axis-name");
    for (const value of [-1, 1]) {
      label(svg, ox + value * scale, oy + 20, String(value));
      label(svg, ox - 15, oy - value * scale + 5, String(value), "sdr-label", "end");
    }
    label(svg, ox - 10, oy + 20, "0", "sdr-label", "end");
    line(svg, px, py, px, oy, "sdr-guide");
    line(svg, px, py, ox, py, "sdr-guide");
    line(svg, ox, oy, px, oy, "sdr-i sdr-projection");
    line(svg, ox, oy, ox, py, "sdr-q sdr-projection");
    line(svg, ox, oy, px, py, output ? "sdr-output sdr-vector" : "sdr-input sdr-vector");
    const angle = Math.atan2(oy - py, px - ox);
    const backX = px - 13 * Math.cos(angle), backY = py + 13 * Math.sin(angle);
    add(svg, "polygon", { points: `${px},${py} ${backX + 5 * Math.sin(angle)},${backY + 5 * Math.cos(angle)} ${backX - 5 * Math.sin(angle)},${backY - 5 * Math.cos(angle)}`, class: output ? "sdr-output sdr-arrow" : "sdr-input sdr-arrow" });
    add(svg, "circle", { cx: px, cy: py, r: 4, class: output ? "sdr-output sdr-dot" : "sdr-input sdr-dot" });
    label(svg, 200, 305, `I = ${number(z.i)}; Q = ${number(z.q)}; magnitud = ${number(Math.hypot(z.i, z.q))}`);
  }

  function trace(svg, values, n, fs) {
    const left = 45, right = 383, top = 25, bottom = 256;
    const x = (index) => left + index / 36 * (right - left);
    const y = (value) => bottom - (value + 1.2) / 2.4 * (bottom - top);
    for (const value of [-1, 0, 1]) {
      line(svg, left, y(value), right, y(value), value === 0 ? "sdr-axis" : "sdr-grid");
      label(svg, left - 9, y(value) + 5, String(value), "sdr-label", "end");
    }
    for (const microseconds of [0, 5, 10, 15]) {
      const xpos = x(microseconds * fs / 1000000);
      line(svg, xpos, top, xpos, bottom, "sdr-grid");
      label(svg, xpos, bottom + 24, String(microseconds));
    }
    label(svg, 213, 307, "Tiempo (µs)");
    label(svg, 48, 16, "I", "sdr-i sdr-axis-name", "start");
    label(svg, 83, 16, "Q", "sdr-q sdr-axis-name", "start");
    for (const component of ["i", "q"]) {
      const points = values.slice(0, 37).map((z, index) => `${x(index)},${y(z[component])}`).join(" ");
      add(svg, "polyline", { points, class: `sdr-${component} sdr-trace` });
      for (let index = 0; index < 37; index += 1) {
        add(svg, "circle", { cx: x(index), cy: y(values[index][component]), r: index === n ? 5 : 2.1, class: `sdr-${component} sdr-dot` });
      }
    }
    line(svg, x(n), top, x(n), bottom, "sdr-cursor");
  }

  function spectral(svg, coefficients, desired, fs) {
    const left = 48, right = 384, top = 20, bottom = 256;
    const max = Math.max(1.2, ...coefficients.map((point) => point.magnitude * 1.12));
    const x = (frequency) => left + (frequency + fs / 2) / fs * (right - left);
    const y = (value) => bottom - value / max * (bottom - top);
    for (const value of [0, 0.5, 1]) {
      line(svg, left, y(value), right, y(value), "sdr-grid");
      label(svg, left - 9, y(value) + 5, number(value, 1), "sdr-label", "end");
    }
    for (const frequency of [-1200000, -600000, 0, 600000, 1200000]) {
      line(svg, x(frequency), top, x(frequency), bottom, frequency === 0 ? "sdr-cursor" : "sdr-grid");
      label(svg, x(frequency), bottom + 24, String(frequency / 1000));
    }
    // Se oculta solo el residuo numérico; no es un detector para capturas reales.
    for (let index = 0; index < coefficients.length; index += 1) {
      const point = coefficients[index];
      if (point.magnitude < 1e-7) continue;
      const cls = desired[index].magnitude > 1e-7 ? "sdr-output" : "sdr-neighbor";
      line(svg, x(point.frequency), bottom, x(point.frequency), y(point.magnitude), `${cls} sdr-stem`);
      add(svg, "circle", { cx: x(point.frequency), cy: y(point.magnitude), r: 3, class: `${cls} sdr-dot` });
    }
    label(svg, 214, 307, "Frecuencia en baseband (kHz)");
    label(svg, 48, 13, "Magnitud", "sdr-label", "start");
  }

  function mount(root) {
    let params = { ...M.DEFAULTS }, n = 1, timer = null, spectra = null, presetName = "original";
    const controls = Object.fromEntries([...root.querySelectorAll("[data-control]")].map((node) => [node.dataset.control, node]));
    const put = (key, value) => { root.querySelector(`[data-value="${key}"]`).textContent = value; };
    const plots = Object.fromEntries([...root.querySelectorAll("[data-plot]")].map((node) => [node.dataset.plot, node]));
    const readings = Object.fromEntries([...root.querySelectorAll("[data-reading]")].map((node) => [node.dataset.reading, node]));
    const instruction = root.querySelector("[data-instruction]");
    const play = root.querySelector("[data-action='play']");

    function pause() {
      if (timer !== null) clearInterval(timer);
      timer = null;
      play.textContent = "Reproducir lentamente";
      play.setAttribute("aria-pressed", "false");
      root.dataset.playing = "false";
    }

    function items(node, texts) {
      const list = document.createElement("ul");
      for (const text of texts) {
        const item = document.createElement("li");
        item.textContent = text;
        list.appendChild(item);
      }
      node.replaceChildren(list);
    }

    function refresh(recompute = false) {
      if (!root.isConnected) { pause(); return; }
      const z = M.sample(params, n);
      const values = M.block(params);
      if (recompute || spectra === null) {
        spectra = {
          before: M.spectrum(values.input), after: M.spectrum(values.output),
          desiredBefore: M.spectrum(values.desiredInput), desiredAfter: M.spectrum(values.desiredOutput)
        };
      }
      const frequency = params.toneHz + params.mixHz;
      const wrapped = M.wrapFrequency(frequency, params.fs);
      const centered = frequency === 0;
      for (const [key, control] of Object.entries(controls)) {
        if (key === "sample") control.value = String(n);
        else if (key === "neighbors") control.checked = params.neighbors;
        else control.value = String(key === "toneHz" || key === "mixHz" ? params[key] / 1000 : params[key]);
      }
      put("tone", hz(params.toneHz)); put("mix", hz(params.mixHz)); put("phase", `${params.phaseDeg}°`);
      put("sample", `n = ${n}; t = ${number(z.t * 1000000)} µs`);
      root.querySelectorAll("[data-local-sample]").forEach((node) => { node.textContent = `n = ${n}`; });
      root.querySelectorAll("[data-preset-select]").forEach((node) => { node.value = presetName; });
      put("frequency", `${hz(params.toneHz)} + (${hz(params.mixHz)}) = ${hz(frequency)}`);
      put("phase-sum", `${number(z.phaseInput * 180 / Math.PI, 1)}° + (${number(z.phaseMix * 180 / Math.PI, 1)}°) = ${number(z.phaseOutput * 180 / Math.PI, 1)}°`);
      put("input", complex(z.input)); put("output", complex(z.output));
      root.dataset.mode = params.mode;
      root.dataset.sample = String(n);
      root.dataset.centered = String(centered);

      plots.iq.replaceChildren();
      chart(plots.iq, "Antes: muestra del objetivo", (svg) => plane(svg, z.input, false));
      chart(plots.iq, "Después: la misma muestra mezclada", (svg) => plane(svg, z.output, true));
      plots.time.replaceChildren();
      chart(plots.time, "Antes: I y Q del objetivo", (svg) => trace(svg, values.desiredInput, n, params.fs));
      chart(plots.time, "Después: I y Q del objetivo", (svg) => trace(svg, values.desiredOutput, n, params.fs));
      if (recompute || !plots.spectrum.querySelector("svg")) {
        plots.spectrum.replaceChildren();
        chart(plots.spectrum, "Antes de la mezcla", (svg) => spectral(svg, spectra.before, spectra.desiredBefore, params.fs));
        chart(plots.spectrum, "Después de la mezcla", (svg) => spectral(svg, spectra.after, spectra.desiredAfter, params.fs));
      }

      items(readings.iq, [
        `Cada flecha representa una sola muestra del objetivo. La posición horizontal es I; la vertical es Q. Se observa n = ${n}, no dos instantes distintos.`,
        `Antes: I = ${number(z.input.i)} y Q = ${number(z.input.q)}. Después: I = ${number(z.output.i)} y Q = ${number(z.output.q)}.`,
        `El oscilador suma ${number(z.phaseMix * 180 / Math.PI, 1)}° a la fase de esta muestra. Los ejes I y Q siguen siendo perpendiculares; no se elimina su cuadratura.`,
        "La longitud de ambas flechas es 1. La mezcla modifica su orientación, no su magnitud."
      ]);
      const timeExplanation = params.mode === "fm"
        ? centered ? "El centro está en 0 Hz, pero I y Q siguen variando: se conserva la fase de la modulación. Centrar no equivale a recuperar el mensaje." : "La fase incluye el desplazamiento de frecuencia y la modulación. La mezcla cambia el primero; no elimina la segunda."
        : centered ? `El tono queda fijo: I = ${number(Math.cos(params.phaseDeg * Math.PI / 180))} y Q = ${number(Math.sin(params.phaseDeg * Math.PI / 180))} en todas las muestras. Estos valores dependen de la fase inicial de ${params.phaseDeg}°.` : `La frecuencia de salida es ${hz(wrapped)}. Las muestras de salida siguen girando; todavía no se centró este tono.`;
      items(readings.time, [
        "Las curvas muestran las coordenadas de la flecha durante 37 muestras. Azul corresponde a I y naranja a Q; no son dos emisoras.",
        "La línea vertical señala la muestra que aparece en el plano I/Q. Al avanzar una muestra, los puntos destacados y la flecha cambian juntos.",
        timeExplanation,
        "Las líneas rectas solo unen las muestras para facilitar la lectura. No representan una nueva señal triangular."
      ]);
      items(readings.spectrum, [
        params.neighbors ? "Aquí sí aparecen todas las componentes: el objetivo en morado y los otros tonos en gris. Las gráficas I/Q anteriores siguen mostrando solo el objetivo, aislado por construcción." : "Aquí se muestra solo el objetivo. Ocultar los otros tonos es una opción del ejemplo, no el resultado de un filtro.",
        `El centro del objetivo pasa de ${hz(params.toneHz)} a ${hz(wrapped)}. ${params.mode === "fm" ? "La señal modulada ocupa varias frecuencias; centrar su banda no convierte todas sus componentes en DC." : "Cada línea vertical es un tono en frecuencia, no un pulso en el tiempo."}`,
        "El espectro usa un bloque completo de 240 muestras (100 µs); el avance de la muestra seleccionada no cambia ese bloque ni su espectro.",
        wrapped !== frequency ? `La suma da ${hz(frequency)}, fuera de [−1200, +1200) kHz. Por periodicidad discreta se representa en ${hz(wrapped)}; no se adquirió otra banda RF.` : "La mezcla no elimina las otras componentes ni selecciona el canal. Para seleccionar una banda todavía hace falta filtrar."
      ]);
    }

    function choosePreset(name) {
      pause();
      const preset = PRESETS[name];
      if (!preset) return;
      presetName = name;
      params = { ...M.DEFAULTS, mixHz: preset.mixHz, phaseDeg: preset.phaseDeg, mode: preset.mode };
      n = 1;
      instruction.textContent = preset.title;
      root.querySelectorAll("[data-preset]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.preset === name)));
      refresh(true);
    }
    root.querySelectorAll("[data-preset]").forEach((button) => {
      button.addEventListener("click", () => choosePreset(button.dataset.preset));
    });
    root.querySelectorAll("[data-preset-select]").forEach((select) => {
      select.addEventListener("change", () => choosePreset(select.value));
    });
    for (const [key, control] of Object.entries(controls)) {
      control.addEventListener("input", () => {
        pause();
        if (key === "sample") n = Number(control.value);
        else if (key === "neighbors") params.neighbors = control.checked;
        else if (key === "mode") params.mode = control.value;
        else params[key] = Number(control.value) * (key === "toneHz" || key === "mixHz" ? 1000 : 1);
        if (key !== "sample") {
          presetName = "";
          instruction.textContent = "Parámetros modificados: se observa el efecto en las tres representaciones.";
          root.querySelectorAll("[data-preset]").forEach((b) => b.setAttribute("aria-pressed", "false"));
        }
        refresh(key !== "sample");
      });
    }
    root.querySelectorAll("[data-step]").forEach((button) => button.addEventListener("click", () => {
      pause(); n = (n + Number(button.dataset.step) + 37) % 37; refresh();
    }));
    play.addEventListener("click", () => {
      if (timer !== null) { pause(); return; }
      play.textContent = "Pausar";
      play.setAttribute("aria-pressed", "true");
      root.dataset.playing = "true";
      timer = setInterval(() => { n = (n + 1) % 37; refresh(); }, 200);
    });
    instruction.textContent = PRESETS.original.title;
    refresh(true);
    pause();
    root.dataset.ready = "true";
    root.querySelector("[data-controls]").hidden = false;
    root.querySelectorAll("[data-local-controls]").forEach((node) => { node.hidden = false; });
    root.querySelector("[data-fallback]").hidden = true;
    return { root, pause };
  }

  function initialize() {
    const root = document.querySelector("[data-sdr-mixer]");
    if (mounted && mounted.root === root) return;
    if (mounted) mounted.pause();
    mounted = root && M ? mount(root) : null;
  }
  document.addEventListener("visibilitychange", () => { if (document.hidden && mounted) mounted.pause(); });
  if (typeof document$ !== "undefined") document$.subscribe(initialize);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize);
  else initialize();
})();
