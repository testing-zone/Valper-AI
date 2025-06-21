import React, { useState, useRef } from 'react';
import { Button, Box } from '@mui/material';
import { Mic, MicOff, Stop } from '@mui/icons-material';

const VoiceRecorder = ({ onRecordingComplete, disabled, isProcessing }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
        onRecordingComplete(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Error accessing microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <Box>
      <Button
        variant={isRecording ? "contained" : "outlined"}
        color={isRecording ? "secondary" : "primary"}
        startIcon={isRecording ? <Stop /> : <Mic />}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled || isProcessing}
        size="large"
        className={isRecording ? "pulse" : ""}
        sx={{
          minWidth: 150,
          height: 50,
          fontSize: '1.1rem',
        }}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </Button>
      
      {isRecording && (
        <Box className="voice-visualizer" sx={{ mt: 2 }}>
          <div className="wave-bar"></div>
          <div className="wave-bar"></div>
          <div className="wave-bar"></div>
          <div className="wave-bar"></div>
          <div className="wave-bar"></div>
        </Box>
      )}
    </Box>
  );
};

export default VoiceRecorder; 