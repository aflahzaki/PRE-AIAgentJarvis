"""
Voice Interface for J.A.R.V.I.S.

Provides speech-to-text and text-to-speech capabilities
with graceful fallback to text-only mode when dependencies are unavailable.
"""

from interfaces.voice.voice_interface import VoiceInterface

__all__ = ["VoiceInterface"]
