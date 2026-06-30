#!/usr/bin/env python3
"""
J.A.R.V.I.S Voice Interface - Entry Point.

Starts the voice-controlled interface for J.A.R.V.I.S.
Loads environment variables and runs the voice loop with
graceful fallback to text-only mode when voice dependencies
are not installed.

Usage:
    python run_voice.py
"""

import logging
import os
import sys

# Ensure core and interfaces modules can be imported from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the Voice Interface."""
    try:
        from interfaces.voice.voice_interface import VoiceInterface
    except ImportError as e:
        logger.error("Failed to import VoiceInterface: %s", str(e))
        print(f"\nError importing VoiceInterface: {e}")
        print("Ensure rich is installed: pip install rich")
        sys.exit(1)

    try:
        interface = VoiceInterface()
        interface.run()
    except KeyboardInterrupt:
        print("\nJ.A.R.V.I.S Voice Interface stopped.")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
