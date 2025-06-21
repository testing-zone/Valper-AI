import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Divider
} from '@mui/material';
import { VolumeUp, Person, SmartToy } from '@mui/icons-material';

const ConversationHistory = ({ conversation }) => {
  const playAudio = (audioUrl) => {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.play().catch(error => {
        console.error('Error playing audio:', error);
      });
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (conversation.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Conversation History
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Start a conversation by recording your voice!
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Conversation History
        </Typography>
        <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
          {conversation.map((message, index) => (
            <Box key={message.id || index} sx={{ mb: 2 }}>
              <Box
                className={`conversation-message ${
                  message.type === 'user' ? 'user-message' : 'assistant-message'
                }`}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: message.type === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  {message.type === 'user' ? (
                    <Person sx={{ fontSize: 20 }} />
                  ) : (
                    <SmartToy sx={{ fontSize: 20 }} />
                  )}
                  <Typography variant="body2" fontWeight="bold">
                    {message.type === 'user' ? 'You' : 'Valper'}
                  </Typography>
                </Box>
                
                <Typography variant="body1" sx={{ mb: 1 }}>
                  {message.text}
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" className="message-timestamp">
                    {formatTime(message.timestamp)}
                  </Typography>
                  
                  {message.audioUrl && (
                    <Button
                      size="small"
                      startIcon={<VolumeUp />}
                      onClick={() => playAudio(message.audioUrl)}
                      variant="outlined"
                    >
                      Play
                    </Button>
                  )}
                </Box>
              </Box>
              
              {index < conversation.length - 1 && (
                <Divider sx={{ my: 1, opacity: 0.3 }} />
              )}
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default ConversationHistory; 