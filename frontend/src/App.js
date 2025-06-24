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
  ListItemText
} from '@mui/material';
import {
  VolumeUp,
  Psychology
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import VoiceRecorder from './components/VoiceRecorder';
import ConversationHistory from './components/ConversationHistory';
import './App.css';

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
  const [conversation, setConversation] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('Ready');
  const [backendHealth, setBackendHealth] = useState(null);

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      // Try direct backend connection first
      const response = await fetch(`http://localhost:8000/health?t=${Date.now()}`, {
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

  const handleVoiceInput = async (audioBlob) => {
    setIsProcessing(true);
    setStatus('Processing speech...');

    try {
      // Convert speech to text
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.wav');

      const sttResponse = await fetch('/api/v1/stt', {
        method: 'POST',
        body: formData,
      });

      if (!sttResponse.ok) {
        throw new Error('Speech recognition failed');
      }

      const sttData = await sttResponse.json();
      const userMessage = sttData.text;

      // Add user message to conversation
      const newUserMessage = {
        id: Date.now(),
        type: 'user',
        text: userMessage,
        timestamp: new Date(),
      };

      setConversation(prev => [...prev, newUserMessage]);

      // Get AI response
      setStatus('Generating response...');
      const conversationResponse = await fetch('/api/v1/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!conversationResponse.ok) {
        throw new Error('Conversation failed');
      }

      const conversationData = await conversationResponse.json();

      // Add AI response to conversation
      const newAIMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        text: conversationData.text_response,
        audioUrl: conversationData.audio_url,
        timestamp: new Date(),
      };

      setConversation(prev => [...prev, newAIMessage]);
      setStatus('Ready');

    } catch (error) {
      console.error('Error processing voice input:', error);
      setStatus('Error: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const testTTS = async () => {
    setIsProcessing(true);
    setStatus('Testing text-to-speech...');

    try {
      const response = await fetch('/api/v1/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: 'Hello! I am Valper, your AI voice assistant. How can I help you today?',
          voice: 'af_heart'
        }),
      });

      if (!response.ok) {
        throw new Error('TTS test failed');
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();

      setStatus('Ready');
    } catch (error) {
      console.error('TTS test error:', error);
      setStatus('Error: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
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
              Voice Interface
            </Typography>
            
            <Box display="flex" justifyContent="center" gap={2} sx={{ mb: 3 }}>
              <VoiceRecorder
                onRecordingComplete={handleVoiceInput}
                disabled={isProcessing || !backendHealth?.stt_ready}
                isProcessing={isProcessing}
              />
              
              <Button
                variant="outlined"
                startIcon={<VolumeUp />}
                onClick={testTTS}
                disabled={isProcessing || !backendHealth?.tts_ready}
              >
                Test TTS
              </Button>
            </Box>

            {isProcessing && (
              <Box display="flex" justifyContent="center" sx={{ mb: 2 }}>
                <CircularProgress />
              </Box>
            )}
          </Paper>

          {/* Conversation History */}
          <ConversationHistory conversation={conversation} />

          {/* Instructions */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                How to Use Valper
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="🎤 Voice Recording" 
                    secondary="Click the microphone button to start recording your voice message"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="🔊 Speech Synthesis" 
                    secondary="Test the text-to-speech functionality with the TTS button"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="💬 Conversation" 
                    secondary="Valper will respond to your voice messages with both text and audio"
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