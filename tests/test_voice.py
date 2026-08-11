import asyncio

from backend.routers.voice import handle_voice_turn
from backend.services.stt import STTService


class FakeTranscriptions:
    def __init__(self, response):
        self.response = response
        self.filename = None

    def create(self, **kwargs):
        self.filename = kwargs["file"][0]
        return self.response


class FakeClient:
    def __init__(self, response):
        self.audio = type("Audio", (), {"transcriptions": FakeTranscriptions(response)})()


def test_stt_uses_audio_webm_and_reads_sdk_object_text():
    service = STTService(api_key="gsk_test")
    assert hasattr(service.client, "audio")
    service.client = FakeClient(type("Transcript", (), {"text": "texto del paciente"})())

    assert service.transcribe(b"audio", "audio.webm") == "texto del paciente"
    assert service.client.audio.transcriptions.filename == "audio.webm"


def test_stt_keeps_text_response_compatibility():
    service = STTService(api_key="gsk_test")
    service.client = FakeClient("texto antiguo")

    assert service.transcribe(b"audio", "audio.webm") == "texto antiguo"


def test_voice_turn_passes_filename_to_stt():
    class FakeSTT:
        filename = None

        def transcribe(self, audio_bytes, filename):
            self.filename = filename
            return "me siento bien"

    class FakeWebSocket:
        def __init__(self):
            self.json_messages = []

        async def send_json(self, message):
            self.json_messages.append(message)

        async def send_bytes(self, _audio):
            pass

    class FakeTTS:
        def synthesize(self, _text):
            return b"audio"

    class FakeConversation:
        def process_turn(self, _transcript):
            return {
                "response": "Continúe con el control indicado.",
                "triage_level": "verde",
                "needs_clarification": False,
                "escalated": False,
            }

    stt = FakeSTT()
    asyncio.run(handle_voice_turn(FakeWebSocket(), stt, FakeTTS(), FakeConversation(), b"audio", "audio.webm"))

    assert stt.filename == "audio.webm"
