import logging
import os
import tempfile
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class STTService:
    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.provider = (provider or os.getenv("STT_PROVIDER", "local")).lower()
        if self.provider not in {"local", "groq"}:
            raise ValueError("STT_PROVIDER debe ser 'local' o 'groq'.")
        self.local_model_name = os.getenv("LOCAL_WHISPER_MODEL", "small")
        self._local_model = None
        self.client = None
        if self.provider == "groq" and self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except ImportError as exc:
                raise RuntimeError("Groq STT requiere instalar 'groq' o usar STT_PROVIDER=local.") from exc
        self.prompt_tuning = (
            "Colombian post-operative context: calentura, chuzo, ta' hinchao, sangrado, "
            "dolor, nrs, fiebre, ahogo, desangrar, pus, infección, herida, mareo, vómito."
        )

    def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        if self.provider == "local":
            return self._transcribe_local(audio_bytes)
        if not self.client or not self.api_key or self.api_key.startswith(("mock", "gsk_mock")):
            raise RuntimeError("Groq STT no está configurado: define GROQ_API_KEY real o usa STT_PROVIDER=local.")
        try:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(filename, audio_bytes),
                prompt=self.prompt_tuning,
                language="es",
                response_format="text",
            )
            return getattr(transcript, "text", str(transcript)).strip()
        except Exception as exc:
            logger.error("Groq STT transcription error: %s", exc)
            raise RuntimeError(f"STT transcription failed: {exc}") from exc

    def _transcribe_local(self, audio_bytes: bytes) -> str:
        try:
            if self._local_model is None:
                from faster_whisper import WhisperModel
                self._local_model = WhisperModel(
                    self.local_model_name, device="cpu", compute_type="int8"
                )
            with tempfile.NamedTemporaryFile(suffix=".webm") as audio_file:
                audio_file.write(audio_bytes)
                audio_file.flush()
                segments, _ = self._local_model.transcribe(audio_file.name, language="es")
            return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        except ImportError as exc:
            raise RuntimeError(
                "STT local requiere faster-whisper. Instala requirements.txt y vuelve a intentar."
            ) from exc
        except Exception as exc:
            logger.exception("Local STT transcription error: %r", exc)
            raise RuntimeError(
                f"No se pudo transcribir el audio WebM con el modelo local '{self.local_model_name}'. "
                "Verifica que faster-whisper esté instalado, que el modelo esté disponible y que el audio sea WebM válido."
            ) from exc
