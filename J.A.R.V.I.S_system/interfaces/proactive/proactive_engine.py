"""
Proactive Engine - Background scheduler for J.A.R.V.I.S notifications.

Runs on a background thread, periodically checking triggers and
dispatching notifications. Configurable via environment variables:
    - PROACTIVE_ENABLED: Set to 'true' to enable (default: false)
    - PROACTIVE_INTERVAL_MINUTES: Check interval in minutes (default: 15)

Uses the 'schedule' library for periodic task execution.
"""

import logging
import os
import threading
import time
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    logger.warning(
        "schedule library not installed. "
        "Proactive engine is disabled. Install with: pip install schedule"
    )


class ProactiveEngine:
    """Background proactive notification engine.

    Periodically checks various triggers (overdue tasks, unlogged habits,
    upcoming deadlines, etc.) and dispatches notifications.

    Usage:
        engine = ProactiveEngine()
        engine.start()  # Starts background thread
        # ... later ...
        engine.stop()   # Stops background thread gracefully
    """

    def __init__(self) -> None:
        """Initialize the ProactiveEngine with configuration from env vars."""
        self.enabled = os.getenv("PROACTIVE_ENABLED", "false").lower() in (
            "true", "1", "yes"
        )
        self.interval_minutes = int(
            os.getenv("PROACTIVE_INTERVAL_MINUTES", "15")
        )
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._scheduler = schedule.Scheduler() if SCHEDULE_AVAILABLE else None
        self._notification_handlers: List[Callable[[str], None]] = []

        # Default to console notifications
        from interfaces.proactive.notifications import console_notify
        self._notification_handlers.append(console_notify)

        # Add Telegram if configured
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_ALLOWED_USERS", "")
        if bot_token and chat_id:
            from interfaces.proactive.notifications import telegram_notify

            def _telegram_handler(message: str) -> None:
                telegram_notify(message, bot_token, chat_id)

            self._notification_handlers.append(_telegram_handler)

    def add_notification_handler(self, handler: Callable[[str], None]) -> None:
        """Register an additional notification handler.

        Args:
            handler: A callable that takes a message string.
        """
        self._notification_handlers.append(handler)

    def _dispatch(self, message: str) -> None:
        """Send a notification message to all registered handlers.

        Args:
            message: The notification text to dispatch.
        """
        for handler in self._notification_handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(
                    "Notification handler error: %s", str(e)
                )

    def _run_checks(self) -> None:
        """Run all trigger checks and dispatch notifications."""
        from interfaces.proactive.triggers import (
            check_overdue_tasks,
            check_unlogged_habits,
            check_upcoming_deadlines,
            daily_summary,
            mood_check,
        )

        triggers = [
            check_overdue_tasks,
            check_unlogged_habits,
            check_upcoming_deadlines,
            daily_summary,
            mood_check,
        ]

        for trigger_fn in triggers:
            try:
                messages = trigger_fn()
                for msg in messages:
                    self._dispatch(msg)
            except Exception as e:
                logger.error(
                    "Trigger check '%s' failed: %s",
                    trigger_fn.__name__,
                    str(e),
                )

    def _scheduler_loop(self) -> None:
        """Background thread loop that runs scheduled jobs."""
        if self._scheduler is None:
            logger.error("Schedule library not available. Cannot run.")
            return

        # Schedule the check at the configured interval
        self._scheduler.every(self.interval_minutes).minutes.do(self._run_checks)

        # Run an initial check immediately
        self._run_checks()

        while not self._stop_event.is_set():
            self._scheduler.run_pending()
            # Sleep in small increments to allow quick shutdown
            self._stop_event.wait(timeout=1.0)

    def start(self) -> bool:
        """Start the proactive engine background thread.

        Returns:
            True if started successfully, False otherwise.
        """
        if not SCHEDULE_AVAILABLE:
            logger.warning(
                "Cannot start ProactiveEngine: 'schedule' library not installed."
            )
            return False

        if not self.enabled:
            logger.info(
                "Proactive engine is disabled. "
                "Set PROACTIVE_ENABLED=true to enable."
            )
            return False

        if self._thread is not None and self._thread.is_alive():
            logger.warning("Proactive engine is already running.")
            return True

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._scheduler_loop,
            name="ProactiveEngine",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Proactive engine started (interval: %d minutes).",
            self.interval_minutes,
        )
        return True

    def stop(self) -> None:
        """Stop the proactive engine background thread gracefully."""
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            logger.info("Proactive engine stopped.")
        self._thread = None
        if self._scheduler is not None:
            self._scheduler.clear()

    @property
    def is_running(self) -> bool:
        """Check if the engine is currently running."""
        return self._thread is not None and self._thread.is_alive()
