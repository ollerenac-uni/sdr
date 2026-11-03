/* Modelo reproducible de la demostración: sin DOM ni dependencias externas. */
(function (scope) {
  "use strict";
  const TAU = 2 * Math.PI;
  const DEFAULTS = Object.freeze({ fs: 2400000, toneHz: 400000, mixHz: 0, phaseDeg: 0, mode: "tone", neighbors: true });
  const MODULATION = Object.freeze({ frequencyHz: 100000, index: 1.2 });

  function rotate(z, angle) {
    const c = Math.cos(angle), s = Math.sin(angle);
    return { i: z.i * c - z.q * s, q: z.i * s + z.q * c };
  }

  function wrapFrequency(frequency, fs) {
    return ((frequency + fs / 2) % fs + fs) % fs - fs / 2;
  }

  function sample(options, n) {
    const p = { ...DEFAULTS, ...options };
    const t = n / p.fs;
    const messagePhase = p.mode === "fm" ? MODULATION.index * Math.sin(TAU * MODULATION.frequencyHz * t) : 0;
    const phaseInput = p.phaseDeg * Math.PI / 180 + TAU * p.toneHz * t + messagePhase;
    const phaseMix = TAU * p.mixHz * t;
    const input = { i: Math.cos(phaseInput), q: Math.sin(phaseInput) };
    const output = rotate(input, phaseMix);
    return { n, t, input, output, phaseInput, phaseMix, phaseOutput: phaseInput + phaseMix, messagePhase };
  }

  function block(options, count = 240) {
    const p = { ...DEFAULTS, ...options };
    const input = [], output = [], desiredInput = [], desiredOutput = [];
    for (let n = 0; n < count; n += 1) {
      const point = sample(p, n);
      desiredInput.push(point.input);
      desiredOutput.push(point.output);
      const z = { ...point.input };
      if (p.neighbors) {
        z.i += 0.6 * Math.cos(TAU * -600000 * point.t) + 0.4;
        z.q += 0.6 * Math.sin(TAU * -600000 * point.t);
      }
      input.push(z);
      output.push(rotate(z, point.phaseMix));
    }
    return { input, output, desiredInput, desiredOutput };
  }

  function spectrum(samples, fs = DEFAULTS.fs) {
    // DFT directa normalizada. Una FFT del mismo bloque obtiene los mismos coeficientes.
    const count = samples.length;
    const coefficients = [];
    for (let k = -Math.floor(count / 2); k < Math.ceil(count / 2); k += 1) {
      const angle = -TAU * k / count;
      const stepI = Math.cos(angle), stepQ = Math.sin(angle);
      let wi = 1, wq = 0, ci = 0, cq = 0;
      for (const z of samples) {
        ci += z.i * wi - z.q * wq;
        cq += z.i * wq + z.q * wi;
        const nextI = wi * stepI - wq * stepQ;
        wq = wi * stepQ + wq * stepI;
        wi = nextI;
      }
      ci /= count;
      cq /= count;
      coefficients.push({ frequency: k * fs / count, i: ci, q: cq, magnitude: Math.hypot(ci, cq) });
    }
    return coefficients;
  }

  const model = Object.freeze({ DEFAULTS, MODULATION, rotate, wrapFrequency, sample, block, spectrum });
  if (typeof module !== "undefined" && module.exports) module.exports = model;
  scope.SDRMixerModel = model;
})(globalThis);
