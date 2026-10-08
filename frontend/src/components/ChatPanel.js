import React, { useEffect, useRef } from 'react';
import Markdown from './Markdown';
import { Teletype } from './Console';

const TOOL_LABELS = {
  get_weather: 'CLIMA', get_news: 'NOTICIAS', memory_save: 'NOTA GUARDADA',
  remember_fact: 'PERFIL', memory_search: 'MEMORIA', memory_read: 'NOTA',
  memory_list: 'NOTAS', create_reminder: 'RECORDATORIO', list_reminders: 'AGENDA',
  complete_reminder: 'HECHO', deep_research: 'INVESTIGACIÓN', research_status: 'ESTADO',
  jira_pending: 'JIRA',
};

const time = (iso) => (iso ? new Date(iso).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: false }) : '');

export default function ChatPanel({ city, messages, freshId, name, onClear, onNoteClick }) {
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  if (!messages.length) {
    return (
      <div className="empty">
        <p>CANAL ABIERTO. HABLE O ESCRIBA.</p>
        <p className="examples">
          "¿cómo está el clima{city ? ` en ${city}` : ''}?"<br />
          "recuérdame mañana a las 9 llamar al banco"<br />
          "guarda que para reiniciar el servidor de video hago X"<br />
          "investiga a fondo qué modelos de video open source hay"
        </p>
      </div>
    );
  }
  return (
    <div className="chat-panel">
      <div className="history-list">
        {messages.map((m) => (
          <div key={m.id} className={`history-item ${m.role}`}>
            <div className="msg-head">
              <span className="msg-who">{m.role === 'user' ? 'OPERADOR' : name}</span>
              <span className="msg-time">{time(m.created_at)}</span>
            </div>
            {m.role === 'assistant' && m.id === freshId ? (
              <Teletype text={m.content}><Markdown onNoteClick={onNoteClick}>{m.content}</Markdown></Teletype>
            ) : (
              <Markdown onNoteClick={onNoteClick}>{m.content}</Markdown>
            )}
            {m.meta?.tools?.length > 0 && (
              <div className="tool-chips">
                {m.meta.tools.map((t, i) => (
                  <span key={i} className="chip" title={JSON.stringify(t.arguments)}>
                    ▸ {TOOL_LABELS[t.name] || t.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <button className="clear-button" onClick={onClear}>BORRAR REGISTRO</button>
    </div>
  );
}
