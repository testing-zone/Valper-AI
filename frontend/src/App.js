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
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);

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

  const stopAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
      setIsPlayingAudio(false);
    }
  };

  const handleMainButtonClick = () => {
    if (isPlayingAudio) {
      // If audio is playing, stop it
      stopAudio();
    } else if (isRecording) {
      // If recording, stop recording
      stopRecording();
    } else if (!isProcessing) {
      // If idle, start recording
      startRecording();
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
        currentAudioRef.current = audio;
        setIsPlayingAudio(true);
        
        // Handle audio events
        audio.onended = () => {
          setIsPlayingAudio(false);
          currentAudioRef.current = null;
        };
        
        audio.onerror = () => {
          setIsPlayingAudio(false);
          currentAudioRef.current = null;
        };
        
        audio.play().catch(error => {
          console.error('Error playing audio:', error);
          setIsPlayingAudio(false);
          currentAudioRef.current = null;
        });
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
      // Stop current audio if playing
      if (currentAudioRef.current) {
        stopAudio();
      }
      
      const audio = new Audio(generatedAudio);
      currentAudioRef.current = audio;
      setIsPlayingAudio(true);
      
      // Handle audio events
      audio.onended = () => {
        setIsPlayingAudio(false);
        currentAudioRef.current = null;
      };
      
      audio.onerror = () => {
        setIsPlayingAudio(false);
        currentAudioRef.current = null;
      };
      
      audio.play().catch(error => {
        console.error('Error playing audio:', error);
        setIsPlayingAudio(false);
        currentAudioRef.current = null;
      });
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
    
    // Stop any playing audio
    if (currentAudioRef.current) {
      stopAudio();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1 data-text="VALPER AI">VALPER AI</h1>
        <p>NEURAL VOICE ASSISTANT</p>
      </header>

      <div className="services-status">
        <h3>SYSTEM STATUS</h3>
        <div className="status-grid">
          <div className={`status-item ${servicesStatus.stt?.status === 'ready' ? 'ready' : 'not-ready'}`}>
            STT: {servicesStatus.stt?.status === 'ready' ? 'ONLINE' : 'OFFLINE'}
          </div>
          <div className={`status-item ${servicesStatus.tts?.status === 'ready' ? 'ready' : 'not-ready'}`}>
            TTS: {servicesStatus.tts?.status === 'ready' ? 'ONLINE' : 'OFFLINE'}
          </div>
          <div className={`status-item ${servicesStatus.llm?.status === 'ready' ? 'ready' : 'not-ready'}`}>
            LLM: {servicesStatus.llm?.status === 'ready' ? 'ONLINE' : 'OFFLINE'}
          </div>
        </div>
      </div>

      <div className="main-container">
        {/* Main Voice Interface */}
        <div className="voice-interface">
          <div className="main-button-container">
            <button 
              className={`main-record-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''} ${isPlayingAudio ? 'playing' : ''}`}
              onClick={handleMainButtonClick}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <div className="processing-animation">
                  <div className="spinner"></div>
                  <div className="processing-text">THINKING</div>
                </div>
              ) : isPlayingAudio ? (
                <div className="playing-content">
                  <div className="stop-icon">⏹</div>
                  <div className="playing-text">STOP</div>
                </div>
              ) : isRecording ? (
                <div className="recording-content">
                  <div className="pulse-ring"></div>
                  <div className="recording-text">LISTENING</div>
                </div>
              ) : (
                <div className="start-content">
                  <div className="start-text">START</div>
                </div>
              )}
            </button>
          </div>

          {isRecording && (
            <div className="voice-visualizer">
              <div className="wave-bar"></div>
              <div className="wave-bar"></div>
              <div className="wave-bar"></div>
              <div className="wave-bar"></div>
              <div className="wave-bar"></div>
            </div>
          )}

          {isProcessing && (
            <div className="processing-stages">
              <div className="stage">
                <div className="stage-icon">🎤</div>
                <div className="stage-text">Processing Audio</div>
              </div>
              <div className="stage">
                <div className="stage-icon">🧠</div>
                <div className="stage-text">Neural Analysis</div>
              </div>
              <div className="stage">
                <div className="stage-icon">🔊</div>
                <div className="stage-text">Generating Response</div>
              </div>
            </div>
          )}
        </div>

        {/* Conversation History */}
        {conversationHistory.length > 0 && (
          <div className="conversation-section">
            <h2>MEMORY BANK</h2>
            <div className="history-list">
              {conversationHistory.map((msg, index) => (
                <div key={index} className={`history-item ${msg.role}`}>
                  <strong>{msg.role === 'user' ? '👤 HUMAN:' : '🤖 AI:'}</strong>
                  <p>{msg.content}</p>
                </div>
              ))}
            </div>
            <button 
              className="clear-button"
              onClick={clearHistory}
            >
              CLEAR MEMORY
            </button>
          </div>
        )}

        {/* Voice Synthesis Lab - Bottom */}
        <div className="synthesis-lab">
          <h2>VOICE SYNTHESIS LAB</h2>
          <div className="tts-controls">
            <textarea
              value={ttsText}
              onChange={(e) => setTtsText(e.target.value)}
              placeholder="Input text for neural voice synthesis..."
              rows="2"
            />
            <div className="button-group">
              <button onClick={generateTTS} disabled={!ttsText.trim()}>
                SYNTHESIZE
              </button>
              <button 
                onClick={isPlayingAudio ? stopAudio : playAudio} 
                disabled={!generatedAudio}
                className={isPlayingAudio ? 'playing' : ''}
              >
                {isPlayingAudio ? 'STOP' : 'PLAY'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 