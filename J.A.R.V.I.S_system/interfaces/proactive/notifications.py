"""
Notification Dispatch - Send notifications through various channels.

Provides notification handlers for:
    - Console output (terminal with Rich formatting)
    - Telegram (via HTTP API using requests)

Designed for extension - new notification channels can be added
by implementing functions with the signature: (message: str) -> None
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning(
        "requests library not installed. Telegram notifications disabled."
    )


def console_notify(message: str) -> None:
    """Print a notification message to the terminal with formatting.

    Uses Rich library for styled output if available, otherwise
    falls back to plain print.

    Args:
        message: The notification text to display.
    """
    if not message:
        return

    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel(
            message,
            title="[bold cyan]J.A.R.V.I.S Notification[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        ))
    else:
        print("[J.A.R.V.I.S] {}".format(message))


def telegram_notify(
    message: str,
    bot_token: str,
    chat_id: str,
) -> Optional[bool]:
    """Send a notification message via Telegram Bot API.

    Uses the Telegram HTTP API (requests.post) to send a message.
    Gracefully handles missing token, missing chat_id, or network failures.

    Args:
        message: The notification text to send.
        bot_token: Telegram Bot API token.
        chat_id: Target chat/user ID to send the message to.

    Returns:
        True if sent successfully, False on failure, None if not configured.
    """
    if not message:
        return None

    if not bot_token or not chat_id:
        logger.debug(
            "Telegram notification skipped: bot_token or chat_id not configured."
        )
        return None

    if not REQUESTS_AVAILABLE:
        logger.warning(
            "Cannot send Telegram notification: requests library not installed."
        )
        return False

    url = "https://api.telegram.org/bot{}/sendMessage".format(bot_token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.debug("Telegram notification sent successfully.")
            return True
        else:
            logger.warning(
                "Telegram API returned status %d: %s",
                response.status_code,
                response.text[:200],
            )
            return False
    except requests.exceptions.Timeout:
        logger.warning("Telegram notification timed out.")
        return False
    except requests.exceptions.ConnectionError:
        logger.warning("Telegram notification failed: connection error.")
        return False
    except Exception as e:
        logger.warning("Telegram notification failed: %s", str(e))
        return False
