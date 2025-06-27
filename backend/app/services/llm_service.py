import os
import logging
import requests
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class LLMService:
    """LLM service using TotalGPT API"""
    
    def __init__(self):
        self.api_key = os.getenv("TOTALGPT_API_KEY")
        self.api_url = "https://api.totalgpt.ai/v1/chat/completions"
        self.model = "Sao10K-72B-Qwen2.5-Kunou-v1-FP8-Dynamic"
        self.is_ready = False
        
        if self.api_key:
            self.is_ready = True
            logger.info("TotalGPT API key found, LLM service ready")
        else:
            logger.warning("TOTALGPT_API_KEY not found, LLM service not available")
    
    async def generate_response(self, user_message: str, conversation_history: List[Dict] = None) -> Optional[str]:
        """Generate response using TotalGPT"""
        if not self.is_ready:
            logger.error("LLM service not ready - API key missing")
            return None
        
        try:
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": "You are Valper, a helpful and friendly AI voice assistant. Keep your responses concise, natural, and conversational. You should be helpful, informative, and engaging in your interactions."
                }
            ]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-5:]:  # Keep last 5 messages for context
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 7000,
                "temperature": 0.7,
                "top_k": 40,
                "repetition_penalty": 1.2
            }
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Sending request to TotalGPT: {user_message[:50]}...")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["choices"][0]["message"]["content"]
                logger.info(f"TotalGPT response generated successfully")
                return assistant_message
            else:
                logger.error(f"TotalGPT API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return None
    
    def get_info(self) -> Dict:
        """Get information about the LLM service"""
        return {
            "service": "TotalGPT",
            "model": self.model,
            "status": "ready" if self.is_ready else "not available",
            "api_configured": bool(self.api_key)
        }
    
    @property
    def is_available(self) -> bool:
        """Check if the LLM service is available"""
        return self.is_ready 