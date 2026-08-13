# Local Demo Video

`postop-voice-agent-demo.mp4` is a local evidence recording of the application surfaces and test result.

## Reproduce

From the repository root:

```bash
command -v ffmpeg
command -v ffprobe
command -v chromium
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another terminal, capture the real pages:

```bash
mkdir -p demo/captures
for page in admin call docs health; do
  chromium --headless --no-sandbox --disable-gpu --hide-scrollbars \
    --window-size=1440,900 --screenshot="demo/captures/$page.png" \
    "http://127.0.0.1:8000/$page/"
done
```

Use `http://127.0.0.1:8000/docs` rather than `/docs/` if the trailing-slash request redirects. Then run:

```bash
demo/make_video.sh
ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=width,height -of default=noprint_wrappers=1 \
  demo/postop-voice-agent-demo.mp4
```

## Scope and limitations

- The recording uses real local HTTP responses and Chromium screenshots for `/admin`, `/call`, `/docs`, and `/health`.
- The video is silent; adding narration was intentionally skipped because it is not needed for evidence.
- The video does not claim a live voice exchange, model inference, or external service response.
- No credentials, uploads, or patient data are used.
- The video is also published on YouTube as an unlisted video: https://youtu.be/RGncO51IokA
- The `57 passed` frame reflects the local `.venv/bin/pytest -q` run recorded for this demo.
