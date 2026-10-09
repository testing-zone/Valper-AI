import React, { useState } from 'react';
import Markdown from './Markdown';
import { api, formatDate } from '../api';

const KIND = {
  digest: 'BOLETÍN', local: 'LOCAL', jira: 'JIRA',
  reminder: 'RECORDATORIO', research: 'INVESTIGACIÓN', orca: 'ORCA', discord: 'DISCORD', morning: 'BUENOS DÍAS', night: 'BUENAS NOCHES',
};

export default function FeedPanel({ location, items, onSpeak, onOpenResearch }) {
  const [running, setRunning] = useState('');

  const run = async (job) => {
    setRunning(job);
    try { await api(`/briefings/${job}/run`, { method: 'POST' }); }
    catch (e) { alert(e.message); }
    finally { setRunning(''); }
  };

  return (
    <div className="feed-panel">
      <div className="toolbar">
        <button onClick={() => run('digest')} disabled={!!running}>
          {running === 'digest' ? '...' : 'RESUMEN AHORA'}
        </button>
        <button onClick={() => run('local')} disabled={!!running}>
          {running === 'local' ? '...' : 'NOTICIAS LOCALES'}
        </button>
        <button onClick={() => run('jira')} disabled={!!running}>
          {running === 'jira' ? '...' : 'JIRA'}
        </button>
      </div>
      {!items.length && <div className="empty">SIN BOLETINES. LLEGAN SEGÚN EL HORARIO, O SOLICÍTELOS ARRIBA.</div>}
      {items.map((it) => {
        const data = it.data ? JSON.parse(it.data) : {};
        return (
          <article key={it.id} className={`card kind-${it.kind}`}>
            <header>
              <span className="kind">{it.kind === 'local' && location ? location.toUpperCase() : KIND[it.kind] || it.kind}</span>
              <span className="card-title">{it.title}</span>
              <span className="date">{formatDate(it.created_at)}</span>
            </header>
            <Markdown>{it.body}</Markdown>
            <footer>
              <button className="link-button" onClick={() => onSpeak(it.body)}>▸ LEER EN VOZ</button>
              {data.research_id && (
                <button className="link-button" onClick={() => onOpenResearch(data.research_id)}>▸ VER REPORTE</button>
              )}
            </footer>
          </article>
        );
      })}
    </div>
  );
}
