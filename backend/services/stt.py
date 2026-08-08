import os
import logging
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.prompt_tuning = (
            "Colombian post-operative context: calentura, chuzo, ta' hinchao, sangrado, "
            "dolor, nrs, fiebre, ahogo, desangrar, pus, infección, herida, mareo, vómito."
        )

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Transcribes audio bytes using Groq Whisper Large V3 with Colombian slang prompting.
        Falls back to a mock transcript if API key is missing or in test mode.
        """
        if not self.client or not self.api_key or self.api_key.startswith("mock") or self.api_key.startswith("gsk_mock"):
            logger.info("STTService using mock transcription (no valid Groq API key configured).")
            # Return plausible mock patient utterance for testing
            return "Doctor, me duele harto el chuzo y tengo calentura."

        try:
            # Groq audio transcription API call
            # file tuple format: (filename, file_bytes)
            transcript = self.client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(filename, audio_bytes),
                prompt=self.prompt_tuning,
                language="es",
                response_format="text"
            )
            return str(transcript).strip()
        except Exception as e:
            logger.error(f"Groq STT transcription error: {e}")
            raise RuntimeError(f"STT transcription failed: {e}")
