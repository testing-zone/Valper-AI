import React, { useEffect, useState } from 'react';
import Markdown from './Markdown';
import { api, formatDate } from '../api';

const STATUS = { queued: '◌ EN COLA', running: '◐ INVESTIGANDO', done: '● LISTO', error: '✕ ERROR' };

export default function ResearchPanel({ jobs, selectedId, onSelect, refresh }) {
  const [prompt, setPrompt] = useState('');
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    if (!selectedId) { setDetail(null); return; }
    api(`/research/${selectedId}`).then(setDetail).catch(() => setDetail(null));
  }, [selectedId, jobs]);

  const launch = async () => {
    if (!prompt.trim()) return;
    try {
      const r = await api('/research', { method: 'POST', body: { prompt } });
      setPrompt('');
      refresh();
      onSelect(r.job_id);
    } catch (e) { alert(e.message); }
  };

  return (
    <div className="split">
      <aside className="sidebar">
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={4}
                  placeholder="¿Qué investigo a fondo? (Claude Code + búsqueda web)" />
        <button onClick={launch} disabled={!prompt.trim()}>INVESTIGAR</button>
        <ul className="list">
          {jobs.map((j) => (
            <li key={j.id} className={j.id === selectedId ? 'active' : ''} onClick={() => onSelect(j.id)}>
              <div className="list-title">{j.prompt.slice(0, 80)}</div>
              <div className="list-meta">{STATUS[j.status] || j.status} · {formatDate(j.created_at)}</div>
            </li>
          ))}
        </ul>
      </aside>
      <section className="detail">
        {!detail && <div className="empty">Selecciona una investigación.</div>}
        {detail && (
          <>
            <h3>{detail.prompt}</h3>
            <div className="list-meta">
              {STATUS[detail.status]} {detail.cost_usd ? `· equivalente API ~$${detail.cost_usd.toFixed(2)} (con suscripción no se cobra)` : ''}
            </div>
            {detail.status === 'done' && <Markdown>{detail.result}</Markdown>}
            {detail.status === 'error' && <pre className="error">{detail.error}</pre>}
            {(detail.status === 'running' || detail.status === 'queued') &&
              <div className="empty">Claude Code está trabajando. Te aviso cuando termine.</div>}
          </>
        )}
      </section>
    </div>
  );
}
