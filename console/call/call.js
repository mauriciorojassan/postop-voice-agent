let ws = null;
let mediaRecorder = null;
let audioContext = null;
let audioQueue = [];
let isPlaying = false;
let recorderStream = null;
let pendingAudioSends = Promise.resolve();
let endingCall = false;
let lastSpokenResponse = '';

const startBtn = document.getElementById('start-btn');
const endBtn = document.getElementById('end-btn');
const statusCard = document.getElementById('status-card');
const logContainer = document.getElementById('log-container');
const triageBadge = document.getElementById('triage-badge');

function logMessage(sender, text, isAlert = false) {
    if (logContainer.querySelector('.italic')) {
        logContainer.innerHTML = '';
    }
    const div = document.createElement('div');
    div.className = `mb-3 p-3 rounded-lg text-sm ${sender === 'Paciente' ? 'bg-blue-50 text-blue-900 ml-8' : isAlert ? 'bg-red-100 text-red-900 border border-red-300' : 'bg-white text-gray-800 mr-8 border border-gray-200'}`;
    div.innerHTML = `<span class="font-bold block text-xs mb-1 text-gray-500">${sender}</span>${text}`;
    logContainer.appendChild(div);
    logContainer.scrollTop = logContainer.scrollHeight;
}

async function startCall() {
    try {
        endingCall = false;
        statusCard.className = 'mb-6 p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 text-center font-medium';
        statusCard.textContent = 'Conectando llamada...';

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/voice?caso_id=caso_101&paciente_id=pac_05&dia_postop=2`;
        
        ws = new WebSocket(wsUrl);
        ws.binaryType = 'arraybuffer';

        ws.onopen = async () => {
            statusCard.className = 'mb-6 p-4 rounded-lg bg-green-50 border border-green-200 text-green-800 text-center font-medium';
            statusCard.textContent = 'Llamada en curso (Conectado)';
            startBtn.disabled = true;
            startBtn.classList.add('opacity-50', 'cursor-not-allowed');
            endBtn.disabled = false;
            endBtn.classList.remove('opacity-50', 'cursor-not-allowed');

            await setupMicrophone();
        };

        ws.onmessage = async (event) => {
            if (event.data instanceof ArrayBuffer) {
                // Audio chunk received from server (TTS)
                queueAudio(event.data);
            } else {
                try {
                    const data = JSON.parse(event.data);
                    if (data.event === 'transcript') {
                        logMessage('Paciente', data.text);
                    } else if (data.event === 'agent_response') {
                        const isRed = data.triage_level === 'rojo';
                        logMessage('Asistente (Doctor)', data.text, isRed);
                        updateTriage(data.triage_level);
                        speakResponse(data.text);
                    } else if (data.event === 'error') {
                        logMessage('Sistema', data.message || 'Error del backend.', true);
                        statusCard.className = 'mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-center font-medium';
                        statusCard.textContent = data.message || 'Error del backend';
                    } else if (data.event === 'barge_in') {
                        stopAudioPlayback();
                        logMessage('Sistema', 'Interrupción detectada (Barge-in).', true);
                    } else if (data.event === 'call_summary') {
                        logMessage('Sistema', `Resumen de llamada guardado. Triage final: ${data.summary.final_triage}`, false);
                    }
                } catch (e) {
                    console.error('Error parsing WS message:', e);
                }
            }
        };

        ws.onclose = () => {
            endCall(false);
        };

        ws.onerror = (err) => {
            console.error('WebSocket error:', err);
            statusCard.className = 'mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-center font-medium';
            statusCard.textContent = 'Error de conexión';
        };

    } catch (err) {
        console.error('Failed to start call:', err);
        alert('No se pudo acceder al micrófono o iniciar la conexión.');
        endCall(false);
    }
}

async function setupMicrophone() {
    recorderStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    startRecorderSegment();
}

function startRecorderSegment() {
    mediaRecorder = new MediaRecorder(recorderStream, { mimeType: 'audio/webm' });

    mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0 && ws && ws.readyState === WebSocket.OPEN) {
            pendingAudioSends = pendingAudioSends.then(() => event.data.arrayBuffer()).then(buffer => {
                if (ws && ws.readyState === WebSocket.OPEN) ws.send(buffer);
            });
        }
    };

    mediaRecorder.onstop = () => {
        pendingAudioSends.then(() => {
            if (ws && ws.readyState === WebSocket.OPEN) ws.send('EOT');
            if (!endingCall) startRecorderSegment();
        });
    };

    // Each segment is independently finalized before the server transcribes it.
    mediaRecorder.start(1000);
    setTimeout(() => {
        if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
    }, 3000);
}

function endCall(sendClose = true) {
    endingCall = true;
    const socket = ws;
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        recorderStream.getTracks().forEach(track => track.stop());
    }
    if (ws && sendClose) {
        pendingAudioSends.then(() => socket && socket.close());
    }
    mediaRecorder = null;
    recorderStream = null;
    if (!sendClose) ws = null;

    statusCard.className = 'mb-6 p-4 rounded-lg bg-gray-50 border border-gray-200 text-gray-700 text-center font-medium';
    statusCard.textContent = 'Llamada finalizada';
    startBtn.disabled = false;
    startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    endBtn.disabled = true;
    endBtn.classList.add('opacity-50', 'cursor-not-allowed');
}

function queueAudio(arrayBuffer) {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    audioQueue.push(arrayBuffer);
    if (!isPlaying) {
        playNextAudio();
    }
}

async function playNextAudio() {
    if (audioQueue.length === 0) {
        isPlaying = false;
        return;
    }
    isPlaying = true;
    const buffer = audioQueue.shift();
    try {
        const audioBuffer = await audioContext.decodeAudioData(buffer);
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.onended = () => {
            playNextAudio();
        };
        source.start(0);
    } catch (e) {
        console.error('Error playing audio chunk:', e);
        isPlaying = false;
        playNextAudio();
    }
}

function stopAudioPlayback() {
    audioQueue = [];
    isPlaying = false;
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
}

function speakResponse(text) {
    if (!text || text === lastSpokenResponse || !window.speechSynthesis) return;
    lastSpokenResponse = text;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();
    utterance.voice = voices.find(voice => voice.lang.toLowerCase() === 'es-co') ||
        voices.find(voice => voice.lang.toLowerCase().startsWith('es')) || null;
    utterance.lang = utterance.voice?.lang || 'es-CO';
    window.speechSynthesis.speak(utterance);
}

function updateTriage(level) {
    triageBadge.textContent = level.toUpperCase();
    if (level === 'rojo') {
        triageBadge.className = 'font-bold text-red-600';
    } else if (level === 'amarillo') {
        triageBadge.className = 'font-bold text-yellow-600';
    } else {
        triageBadge.className = 'font-bold text-green-600';
    }
}
