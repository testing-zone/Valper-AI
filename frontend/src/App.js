import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [ttsText, setTtsText] = useState('');
  const [generatedAudio, setGeneratedAudio] = useState(null);
  const [transcriptionResult, setTranscriptionResult] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [servicesStatus, setServicesStatus] = useState({});
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const API_BASE_URL = window.location.protocol + '//' + window.location.host + '/api';

  useEffect(() => {
    checkServicesStatus();
  }, []);

  const checkServicesStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/services/status`);
      const data = await response.json();
      setServicesStatus(data);
    } catch (error) {
      console.error('Error checking services status:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processConversation(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };

  const processConversation = async (audioBlob) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.wav');
      formData.append('conversation_history', JSON.stringify(conversationHistory));

      const response = await fetch(`${API_BASE_URL}/conversation`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Update conversation history
      const newHistory = [
        ...conversationHistory,
        { role: 'user', content: result.user_text },
        { role: 'assistant', content: result.assistant_text }
      ];
      setConversationHistory(newHistory);
      
      // Set transcription result
      setTranscriptionResult(`Usuario: ${result.user_text}\nAsistente: ${result.assistant_text}`);
      
      // Play the generated audio
      const audioResponse = await fetch(`${API_BASE_URL}/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: result.assistant_text }),
      });

      if (audioResponse.ok) {
        const audioBlob = await audioResponse.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        setGeneratedAudio(audioUrl);
        
        // Auto-play the response
        const audio = new Audio(audioUrl);
        audio.play();
      }

    } catch (error) {
      console.error('Error processing conversation:', error);
      alert('Error processing conversation. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const generateTTS = async () => {
    if (!ttsText.trim()) {
      alert('Please enter some text to convert to speech');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: ttsText }),
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        setGeneratedAudio(audioUrl);
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error generating TTS:', error);
      alert('Error generating speech. Please try again.');
    }
  };

  const playAudio = () => {
    if (generatedAudio) {
      const audio = new Audio(generatedAudio);
      audio.play();
    }
  };

  const testSTT = async () => {
    if (!generatedAudio) {
      alert('Please generate audio first');
      return;
    }

    try {
      const response = await fetch(generatedAudio);
      const audioBlob = await response.blob();

      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'test.wav');

      const sttResponse = await fetch(`${API_BASE_URL}/stt`, {
        method: 'POST',
        body: formData,
      });

      if (sttResponse.ok) {
        const result = await sttResponse.json();
        setTranscriptionResult(`Transcripción: ${result.text}`);
      } else {
        throw new Error(`HTTP error! status: ${sttResponse.status}`);
      }
    } catch (error) {
      console.error('Error testing STT:', error);
      alert('Error testing STT. Please try again.');
    }
  };

  const clearHistory = () => {
    setConversationHistory([]);
    setTranscriptionResult('');
    setGeneratedAudio(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎤 Valper AI - Asistente Virtual</h1>
        <p>Asistente de voz con STT, LLM y TTS integrados</p>
      </header>

      <div className="services-status">
        <h3>Estado de Servicios:</h3>
        <div className="status-grid">
          <div className={`status-item ${servicesStatus.stt?.status === 'ready' ? 'ready' : 'not-ready'}`}>
            STT: {servicesStatus.stt?.status || 'Desconocido'}
          </div>
          <div className={`status-item ${servicesStatus.tts?.status === 'ready' ? 'ready' : 'not-ready'}`}>
            TTS: {servicesStatus.tts?.status || 'Desconocido'}
          </div>
          <div className={`status-item ${servicesStatus.llm?.status === 'ready' ? 'ready' : 'not-ready'}`}>
            LLM: {servicesStatus.llm?.status || 'Desconocido'}
          </div>
        </div>
      </div>

      <div className="main-container">
        {/* Conversación por Voz */}
        <div className="section">
          <h2>🎤 Conversación por Voz</h2>
          <div className="voice-controls">
            <button 
              className={`record-button ${isRecording ? 'recording' : ''}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isProcessing}
            >
              {isRecording ? '🛑 Detener Grabación' : '🎤 Iniciar Grabación'}
            </button>
            
            {isProcessing && (
              <div className="processing">
                <span>🔄 Procesando conversación...</span>
              </div>
            )}
          </div>
          
          <button 
            className="clear-button"
            onClick={clearHistory}
            disabled={conversationHistory.length === 0}
          >
            🗑️ Limpiar Historial
          </button>
        </div>

        {/* Prueba TTS Manual */}
        <div className="section">
          <h2>🔊 Prueba TTS Manual</h2>
          <div className="tts-controls">
            <textarea
              value={ttsText}
              onChange={(e) => setTtsText(e.target.value)}
              placeholder="Escribe texto para convertir a voz..."
              rows="3"
            />
            <div className="button-group">
              <button onClick={generateTTS} disabled={!ttsText.trim()}>
                🔊 Generar Audio
              </button>
              <button onClick={playAudio} disabled={!generatedAudio}>
                ▶️ Reproducir
              </button>
              <button onClick={testSTT} disabled={!generatedAudio}>
                🎵 Probar STT
              </button>
            </div>
          </div>
        </div>

        {/* Resultados */}
        <div className="section">
          <h2>📝 Resultados</h2>
          <div className="results">
            {transcriptionResult && (
              <div className="transcription">
                <h3>Conversación:</h3>
                <pre>{transcriptionResult}</pre>
              </div>
            )}
            
            {conversationHistory.length > 0 && (
              <div className="history">
                <h3>Historial de Conversación:</h3>
                <div className="history-list">
                  {conversationHistory.map((msg, index) => (
                    <div key={index} className={`history-item ${msg.role}`}>
                      <strong>{msg.role === 'user' ? '👤 Usuario:' : '🤖 Asistente:'}</strong>
                      <p>{msg.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 