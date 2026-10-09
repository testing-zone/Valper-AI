import React, { useCallback, useEffect, useRef, useState } from 'react';
import './App.css';
import { API, api } from './api';
import ChatPanel from './components/ChatPanel';
import FeedPanel from './components/FeedPanel';
import ResearchPanel from './components/ResearchPanel';
import MemoryPanel from './components/MemoryPanel';
import RemindersPanel from './components/RemindersPanel';
import { Clock, LampBank } from './components/Console';
import HeadSchematic from './components/HeadSchematic';
import { EFFECTS, playWithEffect } from './audioFx';

const TABS = [
  ['chat', '01', 'DIÁLOGO'], ['feed', '02', 'BOLETINES'], ['research', '03', 'INVESTIGACIÓN'],
  ['memory', '04', 'MEMORIA'], ['reminders', '05', 'AGENDA'],
];
const LANGS = [['es', 'ES'], ['en', 'EN'], ['auto', 'AUTO']];
const SAMPLES = {
  es: (n, t) => `Buenas noches${t ? `, ${t}` : ''}. Soy ${n}. Todos los sistemas operan con normalidad.`,
  en: (n, t) => `Good evening${t ? `, ${t}` : ''}. ${n} at your service. All systems are operating normally.`,
};

const readPref = (key, fallback) => {
  try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); }
  catch (e) { return fallback; }
};
const writePref = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* ignore */ } };

function App() {
  const [name, setName] = useState('');
  const [identity, setIdentity] = useState({ location: '', timezone: undefined, title: '', cities: [] });
  const [tab, setTab] = useState(() => {
    const fromHash = window.location.hash.slice(1);
    return TABS.some(([k]) => k === fromHash) ? fromHash : readPref('assistant.tab', 'chat');
  });
  const [autoVoice, setAutoVoice] = useState(() => readPref('assistant.autoVoice', true));
  const [prefs, setPrefs] = useState({ language: 'es', voice_es: '', voice_en: '', effect: 'none' });
  const [voices, setVoices] = useState([]);
  const [status, setStatus] = useState({});
  const [messages, setMessages] = useState([]);
  const [freshId, setFreshId] = useState(null);
  const [feed, setFeed] = useState([]);
  const [unread, setUnread] = useState(0);
  const [jobs, setJobs] = useState([]);
  const [selectedResearch, setSelectedResearch] = useState(null);
  const [selectedNote, setSelectedNote] = useState(null);
  const [remindersVersion, setRemindersVersion] = useState(0);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState('');
  const [quiet, setQuiet] = useState({ quiet: false });

  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioRef = useRef(null);
  const autoVoiceRef = useRef(autoVoice);
  autoVoiceRef.current = autoVoice;
  const effectRef = useRef(prefs.effect);
  effectRef.current = prefs.effect;

  useEffect(() => { writePref('assistant.tab', tab); window.history.replaceState(null, '', `#${tab}`); }, [tab]);
  useEffect(() => writePref('assistant.autoVoice', autoVoice), [autoVoice]);
  useEffect(() => { if (name) document.title = name; }, [name]);

  const loadMessages = () => api('/messages?limit=60').then((d) => { setMessages(d.messages); return d.messages; }).catch(() => []);
  const loadFeed = () => api('/feed?limit=40').then((d) => { setFeed(d.items); setUnread(d.unread); }).catch(() => {});
  const loadJobs = () => api('/research').then((d) => setJobs(d.jobs)).catch(() => {});
  const loadStatus = () => api('/services/status').then(setStatus).catch(() => setStatus({}));

  useEffect(() => {
    api('/identity').then((d) => { setName(d.name); setIdentity(d); }).catch(() => setName('ASISTENTE'));
    api('/voices').then((d) => setVoices(d.voices)).catch(() => {});
    api('/prefs').then(setPrefs).catch(() => {});
    api('/quiet').then(setQuiet).catch(() => {});
    loadMessages(); loadFeed(); loadJobs(); loadStatus();
    const t = setInterval(loadStatus, 15000);
    return () => clearInterval(t);
  }, []);

  // ---- audio ---------------------------------------------------------------
  const stopAudio = () => {
    if (audioRef.current) { audioRef.current.stop(); audioRef.current = null; }
    setIsPlaying(false);
  };

  // voice: explicit voice id to preview; otherwise the server picks it from the language prefs
  const speak = useCallback(async (text, voice) => {
    try {
      const res = await fetch(`${API}/tts`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: voice || undefined }),
      });
      if (!res.ok) return;
      const blob = await res.blob();
      if (audioRef.current) audioRef.current.stop();
      setIsPlaying(true);
      audioRef.current = await playWithEffect(blob, effectRef.current, () => {
        setIsPlaying(false);
        audioRef.current = null;
      });
      loadStatus();
    } catch (e) {
      setIsPlaying(false);
    }
  }, []);

  const setQuietFor = async (minutes) => {
    try { setQuiet(await api('/quiet', { method: 'POST', body: { minutes } })); } catch (e) { setError(e.message); }
  };
  const stopEverything = () => { stopAudio(); api('/stop', { method: 'POST' }).catch(() => {}); };

  const updatePrefs = async (changes) => {
    setPrefs((p) => ({ ...p, ...changes }));
    try { setPrefs(await api('/prefs', { method: 'PUT', body: changes })); loadStatus(); }
    catch (e) { setError(e.message); }
  };

  // ---- live events from the backend -----------------------------------------
  useEffect(() => {
    const es = new EventSource(`${API}/events`);
    es.addEventListener('feed', (e) => {
      const item = JSON.parse(e.data);
      setFeed((prev) => [item, ...prev.filter((x) => x.id !== item.id)]);
      setUnread((n) => n + 1);
      if (item.kind === 'reminder') setRemindersVersion((v) => v + 1);
      if (item.speak && autoVoiceRef.current) speak(item.speech || `${item.title}. ${item.body}`);
    });
    es.addEventListener('research', () => loadJobs());
    es.addEventListener('quiet', (e) => setQuiet(JSON.parse(e.data)));
    es.addEventListener('stop_audio', () => {
      if (audioRef.current) { audioRef.current.stop(); audioRef.current = null; }
      setIsPlaying(false);
    });
    return () => es.close();
  }, [speak]);

  useEffect(() => {
    if (tab === 'feed' && unread > 0) {
      api('/feed/read', { method: 'POST' }).then(() => setUnread(0)).catch(() => {});
    }
  }, [tab, unread]);

  // ---- talking to the assistant ---------------------------------------------
  const handleReply = async (result) => {
    const msgs = await loadMessages();
    const last = msgs[msgs.length - 1];
    if (last && last.role === 'assistant') setFreshId(last.id);
    if (result.tools?.some((t) => t.name === 'deep_research')) loadJobs();
    if (result.tools?.some((t) => t.name.includes('reminder'))) setRemindersVersion((v) => v + 1);
    loadStatus();
    if (autoVoice && !quiet.quiet) speak(result.assistant_text);
  };

  const sendText = async () => {
    const text = input.trim();
    if (!text || isProcessing) return;
    setInput('');
    setError('');
    setIsProcessing(true);
    setTab('chat');
    setMessages((m) => [...m, { id: `tmp-${Date.now()}`, role: 'user', content: text }]);
    try {
      await handleReply(await api('/chat', { method: 'POST', body: { message: text } }));
    } catch (e) {
      setError(e.message);
      loadMessages();
    } finally {
      setIsProcessing(false);
    }
  };

  const sendAudio = async (blob) => {
    setIsProcessing(true);
    setError('');
    setTab('chat');
    try {
      const form = new FormData();
      form.append('audio_file', blob, 'recording.webm');
      const res = await fetch(`${API}/conversation`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      await handleReply(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const startRecording = async () => {
    try {
      stopAudio();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => chunksRef.current.push(e.data);
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        sendAudio(new Blob(chunksRef.current, { type: rec.mimeType || 'audio/webm' }));
      };
      rec.start();
      recorderRef.current = rec;
      setIsRecording(true);
    } catch (e) {
      setError('No pude acceder al micrófono. Revisa los permisos del navegador.');
    }
  };

  const stopRecording = () => {
    if (recorderRef.current && recorderRef.current.state === 'recording') recorderRef.current.stop();
    setIsRecording(false);
  };

  const toggleMain = () => {
    if (isPlaying) stopAudio();
    else if (isRecording) stopRecording();
    else if (!isProcessing) startRecording();
  };
  const toggleRef = useRef(toggleMain);
  toggleRef.current = toggleMain;

  // Ctrl+Space toggles the microphone while the tab is focused
  useEffect(() => {
    const onKey = (e) => {
      if (e.ctrlKey && e.code === 'Space') { e.preventDefault(); toggleRef.current(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const clearChat = async () => {
    if (!window.confirm('¿Borrar toda la conversación? (la memoria y las notas se quedan)')) return;
    await api('/messages', { method: 'DELETE' });
    setMessages([]);
  };

  const openNote = (slug) => { setSelectedNote(slug); setTab('memory'); };
  const openResearch = (id) => { setSelectedResearch(id); setTab('research'); };

  const state = isProcessing ? 'processing' : isPlaying ? 'playing' : isRecording ? 'recording' : 'idle';
  const stateLabel = { idle: 'EN ESPERA', recording: 'ESCUCHANDO', processing: 'PROCESANDO', playing: 'TRANSMITIENDO' }[state];
  const voicesFor = (lang) => voices.filter((v) => (lang === 'es' ? v.lang === 'es' : v.lang.startsWith('en')));
  const displayName = (name || '').toUpperCase();

  return (
    <div className={`App state-${state}`}>
      <div className="crt-overlay" aria-hidden="true" />

      <header className="masthead">
        <div className="nameplate">
          <div className="nameplate-name" data-text={displayName}>{displayName}</div>
          <div className="nameplate-sub">SISTEMA DE CONTROL PERSONAL{identity.location ? ` · ${identity.location.toUpperCase()}` : ''} · MOD. III</div>
        </div>
        <Clock timeZone={identity.timezone} />
      </header>

      <LampBank count={96} busy={state !== 'idle'} />

      <main className="deck">
        <section className="console">
          <HeadSchematic
            jobs={jobs}
            status={status}
            active={{
              ear: isRecording,
              brain: isProcessing,
              mouth: isPlaying,
              claude: jobs.some((j) => j.status === 'running' || j.status === 'queued'),
            }}
          />

          <div className="aperture-wrap">
            <button className={`aperture ${state}`} onClick={toggleMain} disabled={isProcessing} title="Ctrl+Espacio">
              <span className="ring r1" /><span className="ring r2" /><span className="ring r3" />
              <span className="grille" />
              <span className="aperture-core" />
            </button>
            <div className="aperture-label">{stateLabel}</div>
            <div className="hint">[CTRL + ESPACIO] PARA HABLAR</div>
          </div>

          <div className="composer">
            <span className="prompt-sigil">&gt;</span>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') sendText(); }}
              placeholder="INSTRUCCIÓN_"
              disabled={isProcessing}
            />
            <button onClick={sendText} disabled={!input.trim() || isProcessing}>TRANSMITIR</button>
          </div>

          <div className="voice-panel">
            <div className="panel-row">
              <label className="panel-label">IDIOMA</label>
              <div className="segmented">
                {LANGS.map(([k, label]) => (
                  <button key={k} className={prefs.language === k ? 'active' : ''} onClick={() => updatePrefs({ language: k })}>{label}</button>
                ))}
              </div>
            </div>
            {['es', 'en'].map((lang) => {
              const key = `voice_${lang}`;
              const list = voicesFor(lang);
              return (
                <div key={lang} className={`voice-row ${prefs.language !== 'auto' && prefs.language !== lang ? 'dim' : ''}`}>
                  <span className="voice-lang">{lang.toUpperCase()}</span>
                  <select value={prefs[key]} onChange={(e) => updatePrefs({ [key]: e.target.value })}>
                    {prefs[key] && !list.some((v) => v.id === prefs[key]) && <option value={prefs[key]}>{prefs[key]}</option>}
                    <optgroup label="Presets">
                      {list.filter((v) => v.preset).map((v) => <option key={v.id} value={v.id}>★ {v.name}</option>)}
                    </optgroup>
                    <optgroup label="Voces">
                      {list.filter((v) => !v.preset).map((v) => (
                        <option key={v.id} value={v.id}>{v.name} {v.gender === 'm' ? '♂' : '♀'} · {v.lang}</option>
                      ))}
                    </optgroup>
                  </select>
                  <button onClick={() => speak(SAMPLES[lang](name, identity.title), prefs[key])}>▶</button>
                </div>
              );
            })}
            <div className="panel-row">
              <label className="panel-label">FILTRO</label>
              <div className="segmented">
                {EFFECTS.map(([k, label]) => (
                  <button key={k} className={prefs.effect === k ? 'active' : ''} onClick={() => updatePrefs({ effect: k })}>{label}</button>
                ))}
              </div>
            </div>
            <div className="panel-row">
              <label className="panel-label">SILENCIO</label>
              <div className="segmented">
                {[[30, '30M'], [60, '1H'], [120, '2H'], [-1, '∞']].map(([m, label]) => (
                  <button key={m} onClick={() => setQuietFor(m)}>{label}</button>
                ))}
                <button className="stop-btn" onClick={stopEverything} title="Parar lo que está diciendo">■ STOP</button>
              </div>
            </div>
            {quiet.quiet && (
              <div className="quiet-banner">
                🔇 {quiet.reason === 'manual'
                  ? (quiet.until === 'forever' ? 'SILENCIADO HASTA NUEVO AVISO' : `SILENCIADO HASTA ${quiet.until.slice(11, 16)}`)
                  : quiet.reason === 'quiet_hours' ? `HORARIO DE SILENCIO (${quiet.quiet_hours})` : 'MICRÓFONO EN USO'}
                {quiet.reason === 'manual' && <button className="link-button" onClick={() => setQuietFor(0)}>REANUDAR</button>}
              </div>
            )}
            <label className="switch">
              <input type="checkbox" checked={autoVoice} onChange={(e) => setAutoVoice(e.target.checked)} />
              <span className="switch-track"><span className="switch-knob" /></span>
              RESPUESTA HABLADA
            </label>
          </div>

          {error && <div className="error-banner" onClick={() => setError('')}>⚠ {error}</div>}
        </section>

        <section className="modules">
          <nav className="tabs">
            {TABS.map(([key, num, label]) => (
              <button key={key} className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>
                <span className="tab-num">{num}</span>{label}
                {key === 'feed' && unread > 0 && <span className="badge">{unread}</span>}
              </button>
            ))}
          </nav>

          <div className="tab-body">
            {tab === 'chat' && (
              <ChatPanel city={identity.cities[0]} messages={messages} freshId={freshId} name={displayName} onClear={clearChat} onNoteClick={openNote} />
            )}
            {tab === 'feed' && <FeedPanel location={identity.location} items={feed} onSpeak={speak} onOpenResearch={openResearch} />}
            {tab === 'research' && (
              <ResearchPanel jobs={jobs} selectedId={selectedResearch} onSelect={setSelectedResearch} refresh={loadJobs} />
            )}
            {tab === 'memory' && <MemoryPanel selectedSlug={selectedNote} onSelect={setSelectedNote} />}
            {tab === 'reminders' && <RemindersPanel version={remindersVersion} />}
          </div>
        </section>
      </main>

      <footer className="footer-strip">
        <span>TOTALGPT · QWEN</span><span>KOKORO</span><span>WHISPER</span><span>CLAUDE CODE</span>
      </footer>
    </div>
  );
}

export default App;
