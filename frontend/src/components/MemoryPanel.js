import React, { useEffect, useState } from 'react';
import Markdown from './Markdown';
import { api, formatDate } from '../api';

export default function MemoryPanel({ selectedSlug, onSelect }) {
  const [notes, setNotes] = useState([]);
  const [note, setNote] = useState(null);
  const [filter, setFilter] = useState('');
  const [editing, setEditing] = useState(null); // {title, content}

  const load = () => api('/notes').then((d) => setNotes(d.notes)).catch(() => {});
  useEffect(() => { load(); }, []);

  useEffect(() => {
    setEditing(null);
    if (!selectedSlug) { setNote(null); return; }
    api(`/notes/${selectedSlug}`).then(setNote).catch(() => setNote({ missing: selectedSlug }));
  }, [selectedSlug]);

  const save = async () => {
    const saved = await api('/notes', { method: 'PUT', body: { title: editing.title, content: editing.content } });
    setEditing(null);
    await load();
    onSelect(saved.slug);
    api(`/notes/${saved.slug}`).then(setNote);
  };

  const shown = notes.filter((n) =>
    !filter || n.title.toLowerCase().includes(filter.toLowerCase()) || n.tags.join(' ').includes(filter.toLowerCase()));

  return (
    <div className="split">
      <aside className="sidebar">
        <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filtrar notas..." />
        <button onClick={() => setEditing({ title: '', content: '' })}>NUEVA NOTA</button>
        <ul className="list">
          {shown.map((n) => (
            <li key={n.slug} className={n.slug === selectedSlug ? 'active' : ''} onClick={() => onSelect(n.slug)}>
              <div className="list-title">{n.title}</div>
              <div className="list-meta">{n.tags.join(', ')} · {formatDate(n.updated_at)}</div>
            </li>
          ))}
        </ul>
      </aside>
      <section className="detail">
        {editing ? (
          <div className="editor">
            <input value={editing.title} placeholder="Título"
                   onChange={(e) => setEditing({ ...editing, title: e.target.value })} />
            <textarea value={editing.content} rows={18}
                      placeholder="Markdown. Enlaza otras notas con [[Título]]"
                      onChange={(e) => setEditing({ ...editing, content: e.target.value })} />
            <div className="toolbar">
              <button onClick={save} disabled={!editing.title.trim()}>GUARDAR</button>
              <button onClick={() => setEditing(null)}>CANCELAR</button>
            </div>
          </div>
        ) : note?.missing ? (
          <div className="empty">
            La nota "{note.missing}" no existe todavía.{' '}
            <button className="link-button" onClick={() => setEditing({ title: note.missing, content: '' })}>crearla</button>
          </div>
        ) : note ? (
          <>
            <div className="toolbar">
              <button onClick={() => setEditing({ title: note.title, content: note.content })}>EDITAR</button>
            </div>
            <Markdown onNoteClick={onSelect}>{note.content}</Markdown>
            {note.backlinks?.length > 0 && (
              <div className="backlinks">
                <strong>Enlazada desde:</strong>{' '}
                {note.backlinks.map((b) => (
                  <button key={b} className="link-button" onClick={() => onSelect(b)}>{b}</button>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="empty">
            Aquí vive lo que el asistente aprende: procedimientos, decisiones, contexto. Dile al asistente "guarda que para X hay que Y"
            y aparecerá aquí. También puedes abrir la carpeta data/memory en Obsidian.
          </div>
        )}
      </section>
    </div>
  );
}
