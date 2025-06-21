import os
from typing import Optional

class Settings:
    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Model Paths
    MODELS_DIR: str = os.getenv("MODELS_DIR", "models")
    DEEPSPEECH_MODEL_PATH: str = os.path.join(MODELS_DIR, "deepspeech-0.9.3-models.pbmm")
    DEEPSPEECH_SCORER_PATH: str = os.path.join(MODELS_DIR, "deepspeech-0.9.3-models.scorer")
    
    # Audio Settings
    TEMP_AUDIO_DIR: str = os.getenv("TEMP_AUDIO_DIR", "temp/audio")
    SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", "16000"))
    
    # CORS Settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
    ]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def __init__(self):
        # Create necessary directories
        os.makedirs(self.MODELS_DIR, exist_ok=True)
        os.makedirs(self.TEMP_AUDIO_DIR, exist_ok=True)

settings = Settings() 