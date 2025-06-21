import React, { useState } from 'react';
import { Button, Box, CircularProgress } from '@mui/material';
import { VolumeUp, VolumeOff } from '@mui/icons-material';

const TTSPlayer = ({ audioUrl, text }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const playAudio = async () => {
    if (!audioUrl) return;

    setIsLoading(true);
    
    try {
      const audio = new Audio(audioUrl);
      
      audio.onloadstart = () => setIsLoading(true);
      audio.oncanplay = () => setIsLoading(false);
      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => {
        setIsLoading(false);
        setIsPlaying(false);
        console.error('Error playing audio');
      };

      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      setIsLoading(false);
      setIsPlaying(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Button
        variant="outlined"
        size="small"
        startIcon={
          isLoading ? (
            <CircularProgress size={16} />
          ) : isPlaying ? (
            <VolumeOff />
          ) : (
            <VolumeUp />
          )
        }
        onClick={playAudio}
        disabled={!audioUrl || isLoading}
      >
        {isLoading ? 'Loading...' : isPlaying ? 'Playing' : 'Play'}
      </Button>
    </Box>
  );
};

export default TTSPlayer; 