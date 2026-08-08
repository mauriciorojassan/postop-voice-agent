import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from backend.services.stt import STTService
from backend.services.tts import TTSService
from backend.services.conversation import ConversationManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting storage: IP -> list of connection timestamps
_CONNECTION_TRACKER: Dict[str, list] = []
MAX_CONNECTIONS_PER_SEC = 10

def check_rate_limit(client_ip: str) -> bool:
    global _CONNECTION_TRACKER
    now = time.time()
    # Clean old timestamps
    timestamps = [t for t in _CONNECTION_TRACKER if now - t < 1.0]
    if len(timestamps) >= MAX_CONNECTIONS_PER_SEC:
        _CONNECTION_TRACKER = timestamps
        return False
    timestamps.append(now)
    _CONNECTION_TRACKER = timestamps
    return True

@router.websocket("/ws/voice")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    caso_id: str = "caso_101",
    paciente_id: str = "pac_05",
    dia_postop: int = 2
):
    client_ip = websocket.client.host if websocket.client else "unknown"
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP {client_ip} on /ws/voice")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Rate limit exceeded")
        return

    await websocket.accept()
    logger.info(f"WebSocket voice connection accepted for caso_id={caso_id}, paciente_id={paciente_id}")

    stt_service = STTService()
    tts_service = TTSService()
    
    # Initialize conversation manager with sample trayectoria snapshot
    trayectoria_snapshot = {
        "procedimiento": "laparoscopia",
        "dolor_nrs": 3,
        "fiebre_c": 37.0,
        "herida": "seca",
        "movilidad": "normal"
    }
    conv_manager = ConversationManager(
        caso_id=caso_id,
        paciente_id=paciente_id,
        dia_postop=dia_postop,
        trayectoria_snapshot=trayectoria_snapshot
    )

    # Send initial greeting audio
    initial_prompt = conv_manager.get_initial_prompt()
    logger.info(f"Initial prompt: {initial_prompt}")
    initial_audio = tts_service.synthesize(initial_prompt)
    await websocket.send_bytes(initial_audio)

    audio_buffer = bytearray()
    current_response_task: Optional[asyncio.Task] = None
    idle_timeout = 60.0 # 60 seconds idle timeout

    try:
        while True:
            try:
                # Wait for next message from client with idle timeout
                message = await asyncio.wait_for(websocket.receive(), timeout=idle_timeout)
            except asyncio.TimeoutError:
                logger.warning(f"WebSocket idle timeout ({idle_timeout}s) reached for client {client_ip}")
                await websocket.send_json({"error": "Idle timeout reached", "status": "closing"})
                break

            # Handle binary audio chunk or text/control message
            if "bytes" in message and message["bytes"]:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)

                # If buffer accumulates enough audio (e.g. > 16KB or end of utterance marker), process turn
                # For streaming responsiveness, or when client sends stop/utterance delimiter
                if len(audio_buffer) >= 8192:
                    # Barge-in: if agent is currently speaking/generating, cancel current response task
                    if current_response_task and not current_response_task.done():
                        logger.info("Barge-in detected: cancelling in-flight agent response task.")
                        current_response_task.cancel()
                        try:
                            await current_response_task
                        except asyncio.CancelledError:
                            pass
                        await websocket.send_json({"event": "barge_in", "message": "Respuesta anterior interrumpida."})

                    # Run processing in background task to allow interruption
                    utterance_bytes = bytes(audio_buffer)
                    audio_buffer.clear()
                    current_response_task = asyncio.create_task(
                        handle_voice_turn(websocket, stt_service, tts_service, conv_manager, utterance_bytes)
                    )

            elif "text" in message and message["text"]:
                text_data = message["text"]
                if text_data == "EOT" or text_data == "stop_speaking":
                    if audio_buffer:
                        if current_response_task and not current_response_task.done():
                            current_response_task.cancel()
                            try:
                                await current_response_task
                            except asyncio.CancelledError:
                                pass
                        utterance_bytes = bytes(audio_buffer)
                        audio_buffer.clear()
                        current_response_task = asyncio.create_task(
                            handle_voice_turn(websocket, stt_service, tts_service, conv_manager, utterance_bytes)
                        )
                elif text_data == "ping":
                    await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for caso_id={caso_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if current_response_task and not current_response_task.done():
            current_response_task.cancel()
        
        # Send final call summary JSON on close if summary was generated
        summary = conv_manager._build_summary("Sesión finalizada por desconexión.")
        try:
            await websocket.send_json({
                "event": "call_summary",
                "summary": summary.dict() if hasattr(summary, "dict") else summary
            })
        except Exception:
            pass
        logger.info(f"Closed voice WebSocket for caso_id={caso_id}. Final triage: {conv_manager.final_triage}")

async def handle_voice_turn(
    websocket: WebSocket,
    stt_service: STTService,
    tts_service: TTSService,
    conv_manager: ConversationManager,
    audio_bytes: bytes
):
    try:
        # 1. STT Transcription
        transcript = stt_service.transcribe(audio_bytes)
        logger.info(f"Transcribed patient speech: {transcript}")
        await websocket.send_json({"event": "transcript", "text": transcript})

        # 2. Conversation & Escalation Processing
        turn_result = conv_manager.process_turn(transcript)
        response_text = turn_result["response"]
        logger.info(f"Agent response text: {response_text}")
        await websocket.send_json({
            "event": "agent_response",
            "text": response_text,
            "triage_level": turn_result["triage_level"],
            "needs_clarification": turn_result["needs_clarification"],
            "escalated": turn_result["escalated"]
        })

        # 3. TTS Synthesis & Streaming Audio Back
        audio_response = tts_service.synthesize(response_text)
        await websocket.send_bytes(audio_response)

        if turn_result.get("summary"):
            await websocket.send_json({
                "event": "call_summary",
                "summary": turn_result["summary"].dict() if hasattr(turn_result["summary"], "dict") else turn_result["summary"]
            })

    except asyncio.CancelledError:
        logger.info("Voice turn processing cancelled due to barge-in.")
        raise
    except Exception as e:
        logger.error(f"Error handling voice turn: {e}")
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass
