// Voice effects applied in the browser with the Web Audio API.
//   colossus: ring modulation + metallic comb delay + slightly lower pitch (1970 mainframe voice)
//   radio:    band-limited, saturated transmission
//   sala:     warm voice in a large hall (butler in a mansion)

export const EFFECTS = [
  ['none', 'NATURAL'],
  ['colossus', 'COLOSSUS'],
  ['radio', 'RADIO'],
  ['sala', 'MANSIÓN'],
];

let ctx = null;
const getCtx = () => {
  if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
  return ctx;
};

function impulse(ac, seconds, decay) {
  const len = Math.floor(ac.sampleRate * seconds);
  const buf = ac.createBuffer(2, len, ac.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const data = buf.getChannelData(ch);
    for (let i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay);
  }
  return buf;
}

function saturator(ac, amount) {
  const node = ac.createWaveShaper();
  const curve = new Float32Array(1024);
  for (let i = 0; i < curve.length; i++) {
    const x = (i / curve.length) * 2 - 1;
    curve[i] = ((1 + amount) * x) / (1 + amount * Math.abs(x));
  }
  node.curve = curve;
  return node;
}

function chain(ac, source, effect) {
  const out = ac.createGain();
  out.connect(ac.destination);

  if (effect === 'colossus') {
    source.playbackRate.value = 0.94;
    const dry = ac.createGain(); dry.gain.value = 0.55;
    const ring = ac.createGain(); ring.gain.value = 0;
    const osc = ac.createOscillator(); osc.frequency.value = 48; osc.connect(ring.gain); osc.start();
    const ringLevel = ac.createGain(); ringLevel.gain.value = 0.7;
    const comb = ac.createDelay(); comb.delayTime.value = 0.011;
    const fb = ac.createGain(); fb.gain.value = 0.45;
    const eq = ac.createBiquadFilter(); eq.type = 'peaking'; eq.frequency.value = 1800; eq.gain.value = 5;
    source.connect(dry); source.connect(ring); ring.connect(ringLevel);
    dry.connect(eq); ringLevel.connect(eq);
    eq.connect(comb); comb.connect(fb); fb.connect(comb);
    eq.connect(out); comb.connect(out);
    return () => osc.stop();
  }
  if (effect === 'radio') {
    const hp = ac.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 450;
    const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 3200;
    const sat = saturator(ac, 6);
    const level = ac.createGain(); level.gain.value = 0.7;
    source.connect(hp); hp.connect(lp); lp.connect(sat); sat.connect(level); level.connect(out);
    return null;
  }
  if (effect === 'sala') {
    const warm = ac.createBiquadFilter(); warm.type = 'lowshelf'; warm.frequency.value = 220; warm.gain.value = 4;
    const verb = ac.createConvolver(); verb.buffer = impulse(ac, 2.2, 3);
    const wet = ac.createGain(); wet.gain.value = 0.22;
    source.connect(warm); warm.connect(out); warm.connect(verb); verb.connect(wet); wet.connect(out);
    return null;
  }
  source.connect(out);
  return null;
}

// Plays an audio blob with an effect. Returns {stop()}; calls onEnd when finished.
export async function playWithEffect(blob, effect, onEnd) {
  const ac = getCtx();
  if (ac.state === 'suspended') await ac.resume();
  const buffer = await ac.decodeAudioData(await blob.arrayBuffer());
  const source = ac.createBufferSource();
  source.buffer = buffer;
  const cleanup = chain(ac, source, effect);
  let done = false;
  const finish = () => {
    if (done) return;
    done = true;
    if (cleanup) cleanup();
    onEnd && onEnd();
  };
  source.onended = finish;
  source.start();
  return { stop: () => { try { source.stop(); } catch (e) { /* already stopped */ } finish(); } };
}
