import inspect
from backend.services.tts import TTSService


def test_piper_subprocess_no_shell():
    """Piper subprocess must never use shell=True (injection safety)."""
    tts = TTSService()
    source = inspect.getsource(tts.synthesize_piper)
    non_comment = [
        line.strip() for line in source.splitlines()
        if not line.strip().startswith("#") and "shell=True" in line
    ]
    assert non_comment == [], "shell=True found in synthesize_piper"
    assert "subprocess.run" in source
