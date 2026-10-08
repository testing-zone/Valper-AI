import React, { useEffect, useMemo, useState } from 'react';

// Bank of blinking indicator lamps, like the Colossus mainframe walls.
export function LampBank({ count = 64, busy = false }) {
  const lamps = useMemo(() => Array.from({ length: count }, (_, i) => ({
    delay: `-${((i * 7919) % 2300) / 1000}s`,
    duration: `${1.2 + ((i * 104729) % 2600) / 1000}s`,
    tone: i % 11 === 0 ? 'red' : i % 5 === 0 ? 'cyan' : 'amber',
  })), [count]);
  return (
    <div className={`lamp-bank ${busy ? 'busy' : ''}`} aria-hidden="true">
      {lamps.map((l, i) => (
        <span key={i} className={`lamp ${l.tone}`} style={{ animationDelay: l.delay, animationDuration: l.duration }} />
      ))}
    </div>
  );
}

export function Clock({ timeZone }) {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const time = now.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZone });
  const date = now.toLocaleDateString('es-CO', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric', timeZone });
  return (
    <div className="clock">
      <div className="clock-time">{time}</div>
      <div className="clock-date">{date.toUpperCase()}</div>
    </div>
  );
}

// Reveals text like a teletype printer, then hands off to `children` (rendered markdown).
export function Teletype({ text, children, speed = 12 }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    setShown(0);
    const step = Math.max(1, Math.round(text.length / 400));
    const t = setInterval(() => {
      setShown((n) => {
        if (n + step >= text.length) { clearInterval(t); return text.length; }
        return n + step;
      });
    }, speed);
    return () => clearInterval(t);
  }, [text, speed]);
  if (shown >= text.length) return children;
  return <div className="teletype">{text.slice(0, shown)}<span className="cursor">█</span></div>;
}
