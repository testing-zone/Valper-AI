import React, { useEffect, useState } from 'react';
import { api, formatDate } from '../api';

const REC = { none: 'una vez', daily: 'diario', weekdays: 'lun-vie', weekly: 'semanal' };

export default function RemindersPanel({ version }) {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ text: '', when: '', recurrence: 'none' });

  const load = () => api('/reminders').then((d) => setItems(d.reminders)).catch(() => {});
  useEffect(() => { load(); }, [version]);

  const add = async () => {
    try {
      await api('/reminders', { method: 'POST', body: form });
      setForm({ text: '', when: '', recurrence: 'none' });
      load();
    } catch (e) { alert(e.message); }
  };

  const done = async (id) => { await api(`/reminders/${id}`, { method: 'DELETE' }); load(); };

  return (
    <div className="reminders-panel">
      <div className="reminder-form">
        <input value={form.text} placeholder="¿Qué te recuerdo?"
               onChange={(e) => setForm({ ...form, text: e.target.value })} />
        <input type="datetime-local" value={form.when}
               onChange={(e) => setForm({ ...form, when: e.target.value })} />
        <select value={form.recurrence} onChange={(e) => setForm({ ...form, recurrence: e.target.value })}>
          {Object.entries(REC).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <button onClick={add} disabled={!form.text.trim() || !form.when}>AGREGAR</button>
      </div>
      {!items.length && <div className="empty">Sin pendientes. También puedes decirle "recuérdame..." al asistente.</div>}
      <ul className="list">
        {items.map((r) => (
          <li key={r.id}>
            <div className="list-title">{r.text}</div>
            <div className="list-meta">
              {formatDate(r.due_at)} · {REC[r.recurrence]}
              <button className="link-button" onClick={() => done(r.id)}>✓ HECHO</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
