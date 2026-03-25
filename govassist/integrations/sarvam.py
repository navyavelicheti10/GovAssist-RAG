import logging
import os
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class SarvamAIClient:
    """Wrapper for Sarvam AI for Speech-to-Text and Text-to-Speech across 12+ Indian languages."""
    
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY", "")
        self.base_url = "https://api.sarvam.ai"
        
        if not self.api_key:
            logger.warning("SARVAM_API_KEY not set. Sarvam integration will be mocked/fail.")

    def speech_to_text(self, audio_file_path: str, language_code: str = "hi-IN") -> str:
        """Transcribes incoming voice note."""
        if not self.api_key:
            return "Mock STT: Provide PM Kisan details."
            
        url = f"{self.base_url}/speech-to-text-translate"
        
        try:
            with open(audio_file_path, "rb") as f:
                files = {"file": f}
                data = {
                    "model": "saaras:v1",
                    "prompt": ""
                }
                headers = {
                    "api-subscription-key": self.api_key
                }
                response = requests.post(url, headers=headers, files=files, data=data)
                
            if response.status_code == 200:
                # Based on Sarvam documentation structure
                return response.json().get("transcript", "")
            else:
                logger.error(f"Sarvam STT failed: {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Sarvam STT Exception: {e}")
            return ""

    def text_to_speech(self, text: str, output_file_path: str, language_code: str = "hi-IN", speaker: str = "meera"):
        """Generates audio from bundled synthesis output."""
        if not self.api_key:
            logger.info("Mock TTS: Saving empty file.")
            with open(output_file_path, "wb") as f:
                f.write(b"")
            return output_file_path
            
        url = f"{self.base_url}/text-to-speech"
        
        payload = {
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": speaker,
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": "bulbul:v1"
        }
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                audio_base64 = response.json().get("audios", [])[0]
                import base64
                with open(output_file_path, "wb") as f:
                    f.write(base64.b64decode(audio_base64))
                return output_file_path
            else:
                logger.error(f"Sarvam TTS failed: {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Sarvam TTS Exception: {e}")
            return ""

sarvam_client = SarvamAIClient()
