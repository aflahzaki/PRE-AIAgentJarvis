"""
Telegram Bot - Main bot class for J.A.R.V.I.S.

Uses python-telegram-bot >= 20.0 async API.
Loads TELEGRAM_BOT_TOKEN from environment.
Registers command and message handlers from handlers.py.
Integrates with core.orchestrator.Orchestrator for processing.
"""

import logging
import os
import signal
import sys
from typing import Optional

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from core.orchestrator import Orchestrator
from interfaces.telegram_bot.handlers import (
    start_handler,
    help_handler,
    status_handler,
    tasks_handler,
    addtask_handler,
    journal_handler,
    search_handler,
    message_handler,
    button_callback,
    initialize_allowed_users,
)

logger = logging.getLogger(__name__)


class TelegramBot:
    """Main Telegram Bot class for J.A.R.V.I.S.

    Initializes the bot with TELEGRAM_BOT_TOKEN from environment,
    registers all command handlers, and provides start/stop lifecycle.
    """

    def __init__(self) -> None:
        """Initialize the TelegramBot.

        Raises:
            ValueError: If TELEGRAM_BOT_TOKEN is not set in environment.
        """
        self.token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not self.token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN not set. "
                "Please set it in your .env file or environment."
            )

        # Initialize the orchestrator
        self.orchestrator: Orchestrator = Orchestrator()

        # Cache the allowed users list at startup
        initialize_allowed_users()

        # Build the application
        self.application: Application = (
            Application.builder().token(self.token).build()
        )

        # Register handlers
        self._register_handlers()

        logger.info("TelegramBot initialized successfully.")

    def _register_handlers(self) -> None:
        """Register all command, callback, and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_handler))
        self.application.add_handler(CommandHandler("help", help_handler))
        self.application.add_handler(CommandHandler("status", status_handler))
        self.application.add_handler(CommandHandler("tasks", tasks_handler))
        self.application.add_handler(CommandHandler("addtask", addtask_handler))
        self.application.add_handler(CommandHandler("journal", journal_handler))
        self.application.add_handler(CommandHandler("search", search_handler))

        # Callback query handler for inline keyboard buttons
        self.application.add_handler(CallbackQueryHandler(button_callback))

        # Default message handler (must be last)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )

        logger.info("All handlers registered.")

    def run(self) -> None:
        """Start the bot with polling. Blocks until shutdown.

        Handles graceful shutdown on SIGINT/SIGTERM.
        """
        logger.info("Starting J.A.R.V.I.S Telegram Bot...")
        print("J.A.R.V.I.S Telegram Bot is running. Press Ctrl+C to stop.")

        # Store orchestrator in bot_data for handlers to access
        self.application.bot_data["orchestrator"] = self.orchestrator

        # Run polling (blocks until stop)
        self.application.run_polling(drop_pending_updates=True)

        logger.info("J.A.R.V.I.S Telegram Bot stopped.")

    def stop(self) -> None:
        """Request graceful shutdown of the bot."""
        logger.info("Shutdown requested for J.A.R.V.I.S Telegram Bot.")
        if self.application.running:
            self.application.stop_running()
