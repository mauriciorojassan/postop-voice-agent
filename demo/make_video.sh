#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/demo/postop-voice-agent-demo.mp4"
CAP="$ROOT/demo/captures"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

mkdir -p "$CAP"

ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "color=c=0x101827:s=1280x720:r=30:d=5" \
  -loop 1 -t 7 -i "$CAP/admin.png" \
  -loop 1 -t 7 -i "$CAP/call.png" \
  -loop 1 -t 7 -i "$CAP/docs.png" \
  -loop 1 -t 7 -i "$CAP/health.png" \
  -f lavfi -i "color=c=0x101827:s=1280x720:r=30:d=7" \
  -f lavfi -i "color=c=0x101827:s=1280x720:r=30:d=6" \
  -filter_complex "
    [0:v]drawtext=fontfile=$FONT:text='Post-Operative Voice Follow-Up Agent':fontcolor=white:fontsize=42:x=70:y=245,
      drawtext=fontfile=$FONT:text='Local evidence demo':fontcolor=0x7dd3fc:fontsize=28:x=74:y=315,
      format=yuv420p[v0];
    [1:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x101827,drawtext=fontfile=$FONT:text='REAL CAPTURE  /admin':fontcolor=white:fontsize=26:x=42:y=34:box=1:boxcolor=0x101827@0.85:boxborderw=12,format=yuv420p[v1];
    [2:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x101827,drawtext=fontfile=$FONT:text='REAL CAPTURE  /call':fontcolor=white:fontsize=26:x=42:y=34:box=1:boxcolor=0x101827@0.85:boxborderw=12,format=yuv420p[v2];
    [3:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x101827,drawtext=fontfile=$FONT:text='REAL CAPTURE  /docs':fontcolor=white:fontsize=26:x=42:y=34:box=1:boxcolor=0x101827@0.85:boxborderw=12,format=yuv420p[v3];
    [4:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x101827,drawtext=fontfile=$FONT:text='REAL CAPTURE  /health':fontcolor=white:fontsize=26:x=42:y=34:box=1:boxcolor=0x101827@0.85:boxborderw=12,format=yuv420p[v4];
    [5:v]drawtext=fontfile=$FONT:text='Architecture':fontcolor=white:fontsize=42:x=70:y=120,drawtext=fontfile=$FONT:text='FastAPI  |  /ws/voice  |  STT  |  TTS  |  RAG  |  escalation':fontcolor=0x7dd3fc:fontsize=27:x=72:y=220,drawtext=fontfile=$FONT:text='Admin knowledge console and browser call surface':fontcolor=white:fontsize=27:x=72:y=285,drawtext=fontfile=$FONT:text='Local-only demo. No external calls required for these captures.':fontcolor=0xb8c5d6:fontsize=22:x=72:y=360,format=yuv420p[v5];
     [6:v]drawtext=fontfile=$FONT:text='Verification':fontcolor=white:fontsize=42:x=70:y=120,drawtext=fontfile=$FONT:text='.venv/bin/uvicorn backend.main\:app --host 127.0.0.1 --port 8000':fontcolor=0x7dd3fc:fontsize=22:x=72:y=220,drawtext=fontfile=$FONT:text='.venv/bin/pytest -q':fontcolor=0x7dd3fc:fontsize=22:x=72:y=270,drawtext=fontfile=$FONT:text='57 passed':fontcolor=0x86efac:fontsize=48:x=72:y=355,drawtext=fontfile=$FONT:text='Observed locally on the recorded run':fontcolor=0xb8c5d6:fontsize=22:x=72:y=430,format=yuv420p[v6];
    [v0][v5][v1][v2][v3][v4][v6]concat=n=7:v=1:a=0[outv]
  " -map "[outv]" -c:v libx264 -preset medium -crf 22 -pix_fmt yuv420p -movflags +faststart "$OUT"

printf 'Wrote %s\n' "$OUT"
