"""
Speech-to-Text module for J.A.R.V.I.S Voice Interface.

Uses faster-whisper for local speech recognition.
Gracefully handles missing dependencies by disabling STT
and allowing text-only fallback.

Environment Variables:
    VOICE_MODEL: Whisper model name (default: 'base')
    VOICE_LANGUAGE: Language code for recognition (default: 'id')
"""

import io
import logging
import os
import wave
from typing import Optional

logger = logging.getLogger(__name__)

# Attempt to import faster-whisper
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning(
        "faster-whisper not installed. STT disabled. "
        "Install with: pip install faster-whisper"
    )

# Attempt to import sounddevice for microphone input
try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    logger.warning(
        "sounddevice not installed. Microphone input disabled. "
        "Install with: pip install sounddevice numpy"
    )


class SpeechToText:
    """Speech-to-Text engine using faster-whisper.

    Handles microphone recording and transcription.
    Falls back gracefully when dependencies are missing.
    """

    def __init__(self) -> None:
        """Initialize the STT engine with model from environment."""
        self.model_name = os.getenv("VOICE_MODEL", "base")
        self.language = os.getenv("VOICE_LANGUAGE", "id")
        self.sample_rate = 16000  # Whisper expects 16kHz audio
        self.model = None
        self.available = False

        if WHISPER_AVAILABLE:
            try:
                self.model = WhisperModel(
                    self.model_name,
                    device="cpu",
                    compute_type="int8",
                )
                self.available = True
                logger.info(
                    "Whisper model '%s' loaded successfully.", self.model_name
                )
            except Exception as e:
                logger.error("Failed to load Whisper model: %s", str(e))
                self.available = False

    def is_available(self) -> bool:
        """Check if STT is available and ready."""
        return self.available and SOUNDDEVICE_AVAILABLE

    def record_audio(self, duration: float = 5.0) -> Optional[bytes]:
        """Record audio from the microphone.

        Args:
            duration: Recording duration in seconds.

        Returns:
            Raw audio bytes in WAV format, or None if recording failed.
        """
        if not SOUNDDEVICE_AVAILABLE:
            logger.warning("Cannot record: sounddevice not available.")
            return None

        try:
            logger.info("Recording for %.1f seconds...", duration)
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()  # Wait until recording is finished

            # Convert to WAV bytes
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())

            return buffer.getvalue()

        except Exception as e:
            logger.error("Recording failed: %s", str(e))
            return None

    def transcribe(self, audio_bytes: bytes) -> Optional[str]:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: WAV audio data as bytes.

        Returns:
            Transcribed text, or None if transcription failed.
        """
        if not self.available or self.model is None:
            logger.warning("Cannot transcribe: Whisper model not available.")
            return None

        try:
            # Write bytes to a temporary buffer for faster-whisper
            buffer = io.BytesIO(audio_bytes)

            segments, info = self.model.transcribe(
                buffer,
                language=self.language,
                beam_size=5,
            )

            # Combine all segments into one text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            result = " ".join(text_parts).strip()

            if result:
                logger.info("Transcribed: %s", result)
                return result
            else:
                logger.info("No speech detected.")
                return None

        except Exception as e:
            logger.error("Transcription failed: %s", str(e))
            return None

    def listen(self, duration: float = 5.0) -> Optional[str]:
        """Record audio from microphone and transcribe it.

        This is the main entry point for STT functionality.

        Args:
            duration: Recording duration in seconds.

        Returns:
            Transcribed text, or None if STT is unavailable or failed.
        """
        if not self.is_available():
            return None

        audio_bytes = self.record_audio(duration=duration)
        if audio_bytes is None:
            return None

        return self.transcribe(audio_bytes)
