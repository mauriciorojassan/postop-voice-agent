import os
import time
import logging
import subprocess
import tempfile
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, model_path: Optional[str] = None, voices_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("KOKORO_MODEL_PATH", "kokoro-v0_19.onnx")
        self.voices_path = voices_path or os.getenv("KOKORO_VOICES_PATH", "voices.bin")
        self.use_fallback = False
        self._kokoro = None
        self._init_tts()

    def _init_tts(self):
        start_time = time.time()
        try:
            # Check if kokoro-onnx is available and model files exist
            if os.path.exists(self.model_path) and os.path.exists(self.voices_path):
                from kokoro_onnx import Kokoro
                self._kokoro = Kokoro(self.model_path, self.voices_path)
            
            elapsed = time.time() - start_time
            if elapsed > 5.0:
                logger.warning(f"Kokoro model load took {elapsed:.2f}s (>5s threshold), activating Piper fallback.")
                self.use_fallback = True
        except Exception as e:
            logger.info(f"Kokoro initialization skipped or failed ({e}), using Piper / mock fallback.")
            self.use_fallback = True

    def synthesize(self, text: str, voice: str = "es-la") -> bytes:
        """
        Synthesizes text to WAV audio bytes using Kokoro-82M ONNX, with Piper or mock fallback.
        Ensures subprocess execution is safe (no shell=True, list args).
        """
        # If in test mode or no model loaded, return mock WAV bytes (or use piper if available)
        if not self._kokoro or self.use_fallback:
            return self.synthesize_piper(text)

        try:
            samples, sample_rate = self._kokoro.create(text, voice=voice, speed=1.0, lang="es")
            # Convert samples to WAV bytes
            import soundfile as sf
            import io
            buf = io.BytesIO()
            sf.write(buf, samples, sample_rate, format='WAV')
            buf.seek(0)
            return buf.read()
        except Exception as e:
            logger.warning(f"Kokoro synthesis failed ({e}), falling back to Piper / mock.")
            return self.synthesize_piper(text)

    def synthesize_piper(self, text: str) -> bytes:
        """
        Synthesizes audio using Piper TTS binary via subprocess with list args (safe, no shell).
        If piper binary is not installed, returns a silent 1-second WAV buffer for testing.
        """
        piper_bin = os.getenv("PIPER_BINARY", "piper")
        model_onnx = os.getenv("PIPER_MODEL", "es_ES-carlfm-medium.onnx")
        
        # Check if piper exists
        piper_path = None
        for path in os.environ.get("PATH", "").split(os.pathsep):
            candidate = Path(path) / "piper"
            if candidate.exists() and candidate.is_file():
                piper_path = str(candidate)
                break

        if not piper_path and not os.path.exists(piper_bin):
            # Return silent WAV / mock audio bytes for testing and local dev without binary
            return self._generate_mock_wav(text)

        cmd = [piper_path or piper_bin, "--model", model_onnx, "--output-file", "-"]
        try:
            # SECURITY: shell=False (default) + arguments passed as list
            process = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10.0,
                shell=False
            )
            if process.returncode == 0 and process.stdout:
                return process.stdout
            else:
                logger.error(f"Piper execution failed: {process.stderr.decode('utf-8', errors='ignore')}")
                return self._generate_mock_wav(text)
        except Exception as e:
            logger.error(f"Piper subprocess error: {e}")
            return self._generate_mock_wav(text)

    def _generate_mock_wav(self, text: str) -> bytes:
        """Generates a valid 1-second silence WAV header + PCM data for testing / mock fallback."""
        import io
        import wave
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wav_file:
            wav_file.setnchannels(1) # Mono
            wav_file.setsampwidth(2) # 16-bit
            wav_file.setframerate(22050) # 22.05 kHz
            # 1 second of silence
            silence = b'\x00' * 22050 * 2
            wav_file.writeframes(silence)
        buf.seek(0)
        return buf.read()
