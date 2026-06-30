#!/usr/bin/env python3
"""
J.A.R.V.I.S Telegram Bot - Entry Point.

Starts the Telegram bot interface for J.A.R.V.I.S.
Loads environment variables and runs the bot with polling.

Usage:
    python run_telegram.py
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
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the Telegram bot."""
    try:
        from interfaces.telegram_bot.bot import TelegramBot
    except ImportError as e:
        logger.error(
            "Failed to import TelegramBot. "
            "Ensure python-telegram-bot is installed: pip install python-telegram-bot"
        )
        logger.error("Import error: %s", str(e))
        sys.exit(1)

    try:
        bot = TelegramBot()
        bot.run()
    except ValueError as e:
        logger.error("Configuration error: %s", str(e))
        print(f"\nError: {e}")
        print("Please set TELEGRAM_BOT_TOKEN in your .env file.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        print("\nJ.A.R.V.I.S Telegram Bot stopped.")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
