"""
Text-to-Speech module for J.A.R.V.I.S Voice Interface.

Uses edge-tts for free Microsoft Azure text-to-speech.
Gracefully handles missing dependencies by disabling TTS.

Environment Variables:
    TTS_VOICE: Edge-TTS voice name (default: 'id-ID-ArdiNeural')
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# Attempt to import edge-tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning(
        "edge-tts not installed. TTS disabled. "
        "Install with: pip install edge-tts"
    )

# Attempt to import audio playback
try:
    import sounddevice as sd
    import numpy as np
    PLAYBACK_AVAILABLE = True
except ImportError:
    PLAYBACK_AVAILABLE = False
    logger.warning(
        "sounddevice not installed. Audio playback disabled. "
        "Install with: pip install sounddevice numpy"
    )


def _get_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create an event loop for async operations."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


class TextToSpeech:
    """Text-to-Speech engine using edge-tts.

    Converts text to speech using Microsoft Azure voices (free via edge-tts).
    Falls back gracefully when dependencies are missing.
    """

    def __init__(self) -> None:
        """Initialize the TTS engine with voice from environment."""
        self.voice = os.getenv("TTS_VOICE", "id-ID-ArdiNeural")
        self.available = EDGE_TTS_AVAILABLE
        self.temp_dir = tempfile.gettempdir()

        if self.available:
            logger.info("TTS initialized with voice: %s", self.voice)
        else:
            logger.info("TTS unavailable - text-only mode.")

    def is_available(self) -> bool:
        """Check if TTS is available and ready."""
        return self.available

    async def _generate_audio(self, text: str) -> Optional[str]:
        """Generate audio file from text using edge-tts.

        Args:
            text: Text to convert to speech.

        Returns:
            Path to the generated audio file, or None if failed.
        """
        if not self.available:
            return None

        try:
            # Create temporary file for audio output
            output_path = os.path.join(self.temp_dir, "jarvis_tts_output.mp3")

            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)

            return output_path

        except Exception as e:
            logger.error("TTS generation failed: %s", str(e))
            return None

    async def _play_audio_file(self, file_path: str) -> None:
        """Play an audio file.

        Args:
            file_path: Path to the audio file to play.
        """
        if not PLAYBACK_AVAILABLE:
            logger.info("Audio playback not available. File saved at: %s", file_path)
            return

        try:
            # Try to use subprocess for mp3 playback (cross-platform)
            import subprocess
            import platform

            system = platform.system()

            if system == "Linux":
                # Try mpv, then ffplay, then aplay
                for player in ["mpv --no-video", "ffplay -nodisp -autoexit", "aplay"]:
                    cmd = player.split() + [file_path]
                    try:
                        proc = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL,
                        )
                        await proc.wait()
                        if proc.returncode == 0:
                            return
                    except FileNotFoundError:
                        continue

            elif system == "Darwin":  # macOS
                proc = await asyncio.create_subprocess_exec(
                    "afplay", file_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                return

            elif system == "Windows":
                # Use Windows Media Player via powershell
                cmd = [
                    "powershell", "-c",
                    f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()"
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                return

            logger.warning("No suitable audio player found on this system.")

        except Exception as e:
            logger.error("Audio playback failed: %s", str(e))

    async def speak_async(self, text: str) -> bool:
        """Asynchronously generate and play speech from text.

        Args:
            text: Text to speak.

        Returns:
            True if speech was generated (and possibly played), False otherwise.
        """
        if not self.available:
            logger.info("TTS not available. Text: %s", text)
            return False

        audio_path = await self._generate_audio(text)
        if audio_path is None:
            return False

        await self._play_audio_file(audio_path)

        # Cleanup temp file
        try:
            os.remove(audio_path)
        except OSError:
            pass

        return True

    def speak(self, text: str) -> bool:
        """Generate and play speech from text (synchronous wrapper).

        This is the main entry point for TTS functionality.
        Runs the async speak operation in an event loop.

        Args:
            text: Text to speak.

        Returns:
            True if speech was generated successfully, False otherwise.
        """
        if not self.available:
            logger.info("TTS not available. Skipping speech output.")
            return False

        try:
            loop = _get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run, self.speak_async(text)
                    )
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(self.speak_async(text))
        except Exception as e:
            logger.error("TTS speak failed: %s", str(e))
            return False
