import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  CircularProgress,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  TextField
} from '@mui/material';
import {
  VolumeUp,
  Psychology
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import './App.css';

// Backend API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://209.137.198.189:8000';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#667eea',
    },
    secondary: {
      main: '#764ba2',
    },
    background: {
      default: 'transparent',
      paper: 'rgba(255, 255, 255, 0.1)',
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
        },
      },
    },
  },
});

function App() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('Ready');
  const [backendHealth, setBackendHealth] = useState(null);
  const [ttsText, setTtsText] = useState('Hello! I am Valper, your AI voice assistant. How can I help you today?');
  const [generatedAudioBlob, setGeneratedAudioBlob] = useState(null);
  const [transcriptionResult, setTranscriptionResult] = useState('');

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      // Add cache busting parameter
      const response = await fetch(`${API_BASE_URL}/api/v1/health?t=${Date.now()}`, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Health check response:', data);
      setBackendHealth(data);
    } catch (error) {
      console.error('Backend health check failed:', error);
      setBackendHealth({ status: 'unhealthy', stt_ready: false, tts_ready: false });
    }
  };

  const testTTS = async () => {
    setIsProcessing(true);
    setStatus('Generating speech...');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: ttsText,
          voice: 'af_heart'
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`TTS test failed: ${response.status} - ${errorText}`);
      }

      const audioBlob = await response.blob();
      console.log('Audio blob size:', audioBlob.size);
      
      // Store the generated audio blob
      setGeneratedAudioBlob(audioBlob);
      setStatus('Speech generated successfully! Ready for STT test.');
      
      // Clear previous transcription
      setTranscriptionResult('');

    } catch (error) {
      console.error('TTS test error:', error);
      setStatus('Error: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const testSTTWithGeneratedAudio = async () => {
    if (!generatedAudioBlob) {
      setStatus('No audio available. Generate speech first.');
      return;
    }

    setIsProcessing(true);
    setStatus('Transcribing audio...');

    try {
      // Convert speech to text
      const formData = new FormData();
      formData.append('audio', generatedAudioBlob, 'audio.wav');

      const sttResponse = await fetch(`${API_BASE_URL}/api/v1/stt`, {
        method: 'POST',
        body: formData,
      });

      if (!sttResponse.ok) {
        throw new Error('Speech recognition failed');
      }

      const sttData = await sttResponse.json();
      const transcribedText = sttData.text;
      
      setTranscriptionResult(transcribedText);
      setStatus('Transcription completed!');

    } catch (error) {
      console.error('Error transcribing audio:', error);
      setStatus('Error: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const playGeneratedAudio = () => {
    if (!generatedAudioBlob) {
      setStatus('No audio available to play.');
      return;
    }

    const audioUrl = URL.createObjectURL(generatedAudioBlob);
    const audio = new Audio(audioUrl);
    
    audio.oncanplay = () => {
      setStatus('Playing audio...');
    };
    
    audio.onended = () => {
      setStatus('Audio finished playing.');
    };
    
    audio.onerror = (e) => {
      console.error('Audio playback error:', e);
      setStatus('Audio playback error');
    };
    
    audio.play();
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        <Container maxWidth="md" sx={{ py: 4 }}>
          {/* Header */}
          <Paper elevation={3} sx={{ p: 3, mb: 3, textAlign: 'center' }}>
            <Box display="flex" alignItems="center" justifyContent="center" gap={2}>
              <Psychology sx={{ fontSize: 40, color: 'primary.main' }} />
              <Typography variant="h3" component="h1" fontWeight="bold">
                Valper AI
              </Typography>
            </Box>
            <Typography variant="h6" color="text.secondary" sx={{ mt: 1 }}>
              Your Intelligent Voice Assistant
            </Typography>
          </Paper>

          {/* Status Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap" alignItems="center">
                <Chip
                  label={`Backend: ${backendHealth?.status || 'Unknown'}`}
                  color={backendHealth?.status === 'healthy' ? 'success' : 'error'}
                  size="small"
                />
                <Chip
                  label={`STT: ${backendHealth?.stt_ready ? 'Ready' : 'Not Ready'}`}
                  color={backendHealth?.stt_ready ? 'success' : 'warning'}
                  size="small"
                />
                <Chip
                  label={`TTS: ${backendHealth?.tts_ready ? 'Ready' : 'Not Ready'}`}
                  color={backendHealth?.tts_ready ? 'success' : 'warning'}
                  size="small"
                />
                <Button size="small" onClick={checkBackendHealth}>
                  Refresh
                </Button>
              </Box>
              {status && (
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Status: {status}
                </Typography>
              )}
              {/* Debug info */}
              <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'text.secondary' }}>
                Debug: {JSON.stringify(backendHealth)}
              </Typography>
            </CardContent>
          </Card>

          {/* Main Interface */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h5" gutterBottom textAlign="center">
              AI Voice Assistant Interface
            </Typography>
            
            {/* TTS Interactive Section */}
            <Box sx={{ mt: 3, p: 2, border: '1px solid rgba(255, 255, 255, 0.2)', borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom textAlign="center">
                Text-to-Speech & Speech-to-Text Test
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  variant="outlined"
                  label="Enter text to convert to speech"
                  value={ttsText}
                  onChange={(e) => setTtsText(e.target.value)}
                  disabled={isProcessing}
                  sx={{ mb: 2 }}
                />
                
                <Box display="flex" justifyContent="center" gap={2} sx={{ mb: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<VolumeUp />}
                    onClick={testTTS}
                    disabled={isProcessing || !backendHealth?.tts_ready || !ttsText.trim()}
                    sx={{ minWidth: 120 }}
                  >
                    {isProcessing ? 'Generating...' : 'Generate Speech'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    onClick={() => setTtsText('Hello! I am Valper, your AI voice assistant. How can I help you today?')}
                    disabled={isProcessing}
                  >
                    Reset
                  </Button>
                </Box>

                {/* Audio Controls */}
                {generatedAudioBlob && (
                  <Box sx={{ mb: 2, p: 2, bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: 1 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Audio Generated Successfully! 🎵
                    </Typography>
                    <Box display="flex" justifyContent="center" gap={2}>
                      <Button
                        variant="outlined"
                        startIcon={<VolumeUp />}
                        onClick={playGeneratedAudio}
                        disabled={isProcessing}
                        size="small"
                      >
                        Play Audio
                      </Button>
                      
                      <Button
                        variant="contained"
                        color="secondary"
                        onClick={testSTTWithGeneratedAudio}
                        disabled={isProcessing || !backendHealth?.stt_ready}
                        size="small"
                      >
                        {isProcessing ? 'Transcribing...' : 'Test STT'}
                      </Button>
                    </Box>
                  </Box>
                )}

                {/* Transcription Result */}
                {transcriptionResult && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(0, 255, 0, 0.1)', borderRadius: 1, border: '1px solid rgba(0, 255, 0, 0.3)' }}>
                    <Typography variant="subtitle2" gutterBottom color="success.main">
                      Transcription Result: 📝
                    </Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                      "{transcriptionResult}"
                    </Typography>
                    
                    {/* Accuracy indicator */}
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Original: "{ttsText}"
                      </Typography>
                    </Box>
                  </Box>
                )}
              </Box>
            </Box>

            {isProcessing && (
              <Box display="flex" justifyContent="center" sx={{ mb: 2 }}>
                <CircularProgress />
              </Box>
            )}
          </Paper>

          {/* Instructions */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                How to Use Valper
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="🔄 TTS → STT Test Loop" 
                    secondary="1. Type text → 2. Generate speech → 3. Play audio → 4. Test STT transcription"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="🎵 Audio Playback" 
                    secondary="Listen to the generated speech before testing transcription"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="📊 Accuracy Test" 
                    secondary="Compare original text with STT transcription results"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="⚡ Status" 
                    secondary="Check the system status to ensure all services are running"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Container>
      </div>
    </ThemeProvider>
  );
}

export default App; 