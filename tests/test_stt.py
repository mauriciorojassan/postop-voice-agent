import os

import pytest

from backend.services.stt import STTService


def test_local_is_default_and_model_name_is_configurable(monkeypatch):
    monkeypatch.delenv("STT_PROVIDER", raising=False)
    monkeypatch.setenv("LOCAL_WHISPER_MODEL", "tiny")
    service = STTService()
    assert service.provider == "local"
    assert service.local_model_name == "tiny"


def test_unknown_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("STT_PROVIDER", "fake")
    with pytest.raises(ValueError, match="local.*groq"):
        STTService()


def test_missing_groq_never_returns_fake_transcript():
    service = STTService(provider="groq", api_key="gsk_mock_key")
    with pytest.raises(RuntimeError, match="Groq STT no está configurado"):
        service.transcribe(b"audio.webm", "audio.webm")


def test_local_extracts_segment_text():
    class Segment:
        def __init__(self, text):
            self.text = text

    class Model:
        def transcribe(self, audio, language):
            assert audio.endswith(".webm")
            with open(audio, "rb") as audio_file:
                assert audio_file.read() == b"real webm"
            assert language == "es"
            return iter([Segment(" hola "), Segment("mundo")]), object()

    service = STTService(provider="local")
    service._local_model = Model()
    assert service.transcribe(b"real webm", "audio.webm") == "hola mundo"


def test_local_cleans_up_temporary_webm_file():
    seen_path = None

    class Model:
        def transcribe(self, audio, language):
            nonlocal seen_path
            seen_path = audio
            assert audio.endswith(".webm")
            assert language == "es"
            return iter([]), object()

    service = STTService(provider="local")
    service._local_model = Model()
    assert service.transcribe(b"real webm", "audio.webm") == ""
    assert seen_path is not None
    assert not os.path.exists(seen_path)
