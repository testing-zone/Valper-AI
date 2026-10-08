import React from 'react';
import { ENGRAVING, SILHOUETTE, TRANSFORM } from './skullArt';

// Gray's Anatomy plate 188 (lateral skull) as a service diagram:
// A external acoustic meatus = STT, B cranial vault = LLM, C dentition = TTS, D occipital port = Claude.
// Lamp states: on (cyan), off (red, blinking + red glow on the region), active (amber pulse).

const PARTS = [
  { key: 'ear', svc: 'stt', letter: 'A', name: 'OÍDO', lamp: [876, 892], tag: [880, 1370], glow: 120 },
  { key: 'brain', svc: 'llm', letter: 'B', name: 'CEREBRO', lamp: [930, 400], tag: [90, 40], glow: 330 },
  { key: 'mouth', svc: 'tts', letter: 'C', name: 'VOZ', lamp: [230, 1060], tag: [-70, 1250], glow: 170 },
  { key: 'claude', svc: 'research', letter: 'D', name: 'CLAUDE', lamp: [1478, 620], tag: [1640, 1290], glow: 110 },
];

const PATHS = {
  ear: 'M 876 870 C 880 740, 900 560, 925 430',
  mouth: 'M 905 425 C 700 560, 420 820, 250 1035',
  claude: 'M 960 410 C 1150 440, 1350 520, 1460 610',
};

const ms = (v) => (v == null ? 'listo' : v < 1000 ? `${v} ms` : `${(v / 1000).toFixed(1)} s`);

function concrete(status, svc, jobs) {
  const s = status[svc] || {};
  if (svc === 'stt') return [`whisper-${s.model || '?'}${s.engine === 'mlx' ? ' · gpu' : ''}`, ms(s.latency_ms)];
  if (svc === 'llm') return [(s.model || '?').replace(/^Qwen-/, '').toLowerCase(), ms(s.latency_ms)];
  if (svc === 'tts') return [`kokoro · ${(s.voice || '?').replace(/\(\d\)/g, '')}`, ms(s.latency_ms)];
  const running = jobs.filter((j) => j.status === 'running' || j.status === 'queued').length;
  return ['claude code', running ? `${running} en curso` : 'en espera'];
}

export default function HeadSchematic({ status, active, jobs = [] }) {
  const state = (p) => (status[p.svc]?.status !== 'ready' ? 'off' : active[p.key] ? 'active' : 'on');
  const st = Object.fromEntries(PARTS.map((p) => [p.key, state(p)]));

  return (
    <figure className="head-schematic">
      <svg viewBox="-160 -40 1880 1460" role="img" aria-label="Diagrama del estado de los servicios">
        <defs>
          <pattern id="hs-grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" className="hs-grid" />
          </pattern>
          <radialGradient id="hs-glow-off"><stop offset="0" stopColor="#ff4a3d" stopOpacity="0.55" /><stop offset="1" stopColor="#ff4a3d" stopOpacity="0" /></radialGradient>
          <radialGradient id="hs-glow-active"><stop offset="0" stopColor="#ffb347" stopOpacity="0.5" /><stop offset="1" stopColor="#ffb347" stopOpacity="0" /></radialGradient>
        </defs>
        <rect x="-160" y="-40" width="1880" height="1460" fill="url(#hs-grid)" />
        <line x1="-160" y1="880" x2="1720" y2="880" className="hs-ref" />

        {PARTS.filter((p) => st[p.key] !== 'on').map((p) => (
          <circle key={p.key} cx={p.lamp[0]} cy={p.lamp[1]} r={p.glow}
                  fill={`url(#hs-glow-${st[p.key]})`} className={`hs-region ${st[p.key]}`} />
        ))}

        <g transform={TRANSFORM}>
          <path d={SILHOUETTE} className="hs-silhouette" />
          <path d={ENGRAVING} className="hs-engraving" />
        </g>

        <path d="M 1490 640 C 1600 700, 1540 1050, 1640 1252" className={`hs-cable ${st.claude}`} />
        <rect x="1462" y="575" width="34" height="90" rx="4" className={`hs-port ${st.claude}`} />

        {Object.entries(PATHS).map(([key, d]) => {
          const flowing = st[key] === 'active' || (key !== 'claude' && st.brain === 'active');
          return <path key={key} d={d} className={`hs-path ${st[key]} ${flowing ? 'flow' : ''}`} />;
        })}

        {PARTS.map((p) => {
          const [lx, ly] = p.lamp;
          const [tx, ty] = p.tag;
          return (
            <g key={p.key} className={`hs-part ${st[p.key]}`}>
              {p.key !== 'claude' && <line x1={lx} y1={ly} x2={tx} y2={ty} className="hs-leader" />}
              <circle cx={tx} cy={ty} r="38" className="hs-tag" />
              <text x={tx} y={ty + 19} textAnchor="middle" className="hs-letter">{p.letter}</text>
              <circle cx={lx} cy={ly} r="40" className="hs-halo" />
              <circle cx={lx} cy={ly} r="17" className="hs-lamp" />
            </g>
          );
        })}
        <text x="1700" y="1405" textAnchor="end" className="hs-small">FIG. 1 · SEGÚN GRAY, LÁM. 188</text>
      </svg>

      <ul className="hs-legend">
        {PARTS.map((p) => {
          const [engine, metric] = concrete(status, p.svc, jobs);
          return (
            <li key={p.key} className={st[p.key]} title={engine}>
              <span className="hs-legend-letter">{p.letter}</span>
              <span className="hs-legend-name">{p.name}</span>
              <span className="hs-legend-metric">{st[p.key] === 'off' ? 'FALLA' : metric}</span>
            </li>
          );
        })}
      </ul>
    </figure>
  );
}
