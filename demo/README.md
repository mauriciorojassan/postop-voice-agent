# Demo Video

[`postop-voice-agent-demo.mp4`](postop-voice-agent-demo.mp4) is a 46-second, 1280x720 local evidence recording of the application surfaces and recorded test result.

## What It Demonstrates

- Real local Chromium captures of `/admin`, `/call`, `/docs`, and `/health`.
- The application surfaces served by the local FastAPI process.
- The recorded `57 passed` validation result.
- The expected local setup and architecture context.

## What It Does Not Demonstrate

- It is silent and does not claim a live voice exchange.
- It does not prove microphone capture, Faster-Whisper inference, browser `speechSynthesis`, or a full browser-driven E2E call.
- It does not use credentials, uploads, or patient data.
- It does not represent telephony or external provider behavior.

## Regenerate

From the repository root, install `ffmpeg`, `ffprobe`, and Chromium, then prepare the environment described in the main [README](../README.md).

Start the local server:

```bash
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another terminal, capture the pages and render the video:

```bash
mkdir -p demo/captures
for page in admin call docs health; do
  chromium --headless --no-sandbox --disable-gpu --hide-scrollbars \
    --window-size=1440,900 --screenshot="demo/captures/$page.png" \
    "http://127.0.0.1:8000/$page"
done
```

Inspect the output:

```bash
ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=width,height -of default=noprint_wrappers=1 \
  demo/postop-voice-agent-demo.mp4
```

The video is also available as an [unlisted YouTube link](https://youtu.be/RGncO51IokA).
