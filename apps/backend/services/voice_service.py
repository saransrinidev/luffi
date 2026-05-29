import logging
import tempfile
import wave
import threading

logger = logging.getLogger(__name__)

try:
    import pyaudio
    import whisper
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    logger.warning("pyaudio/whisper not installed — voice input disabled")


class VoiceService:
    """Voice input using local Whisper model."""

    def __init__(self, model_size: str = "base"):
        self.model = None
        self.is_recording = False
        self._frames = []

        if VOICE_AVAILABLE:
            logger.info(f"Loading Whisper model ({model_size})...")
            self.model = whisper.load_model(model_size)
            logger.info("Whisper ready")

    def start_recording(self):
        """Start recording audio from microphone."""
        if not VOICE_AVAILABLE:
            return

        self.is_recording = True
        self._frames = []
        thread = threading.Thread(target=self._record, daemon=True)
        thread.start()

    def stop_recording(self) -> str | None:
        """Stop recording and transcribe."""
        if not VOICE_AVAILABLE:
            return None

        self.is_recording = False

        if not self._frames:
            return None

        # Save to temp WAV
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"".join(self._frames))

        # Transcribe
        try:
            result = self.model.transcribe(tmp.name)
            text = result["text"].strip()
            logger.info(f"Transcribed: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    def _record(self):
        """Record audio in background."""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
        )

        while self.is_recording:
            data = stream.read(1024, exception_on_overflow=False)
            self._frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()
