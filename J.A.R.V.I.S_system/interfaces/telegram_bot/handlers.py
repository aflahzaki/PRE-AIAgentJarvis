"""
Telegram Bot Handlers for J.A.R.V.I.S.

Implements all command handlers and the default text message handler.
Security: Only responds to users listed in TELEGRAM_ALLOWED_USERS env var.
Messages exceeding Telegram's 4096 char limit are split automatically.
"""

import logging
import os
from typing import List

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Maximum message length for Telegram
MAX_MESSAGE_LENGTH = 4096


def _get_allowed_users() -> List[int]:
    """Get list of allowed Telegram user IDs from environment.

    TELEGRAM_ALLOWED_USERS should be a comma-separated list of user IDs.
    If not set or empty, no users are allowed (bot rejects all messages).

    Returns:
        List of allowed user IDs as integers.
    """
    allowed_str = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
    if not allowed_str.strip():
        return []

    user_ids = []
    for uid in allowed_str.split(","):
        uid = uid.strip()
        if uid:
            try:
                user_ids.append(int(uid))
            except ValueError:
                logger.warning("Invalid user ID in TELEGRAM_ALLOWED_USERS: %s", uid)
    return user_ids


def _is_authorized(user_id: int) -> bool:
    """Check if a user is authorized to use the bot.

    Args:
        user_id: Telegram user ID to check.

    Returns:
        True if user is authorized, False otherwise.
    """
    allowed_users = _get_allowed_users()
    if not allowed_users:
        # If no users configured, deny all access
        logger.warning(
            "TELEGRAM_ALLOWED_USERS not configured. Denying user %s.", user_id
        )
        return False
    return user_id in allowed_users


def _split_message(text: str) -> List[str]:
    """Split a message into chunks that fit Telegram's 4096 char limit.

    Tries to split at newlines or spaces to avoid breaking words.

    Args:
        text: The full message text.

    Returns:
        List of message chunks, each <= 4096 characters.
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= MAX_MESSAGE_LENGTH:
            chunks.append(remaining)
            break

        # Try to split at a newline within the limit
        split_pos = remaining.rfind("\n", 0, MAX_MESSAGE_LENGTH)
        if split_pos == -1 or split_pos < MAX_MESSAGE_LENGTH // 2:
            # Try to split at a space
            split_pos = remaining.rfind(" ", 0, MAX_MESSAGE_LENGTH)
        if split_pos == -1 or split_pos < MAX_MESSAGE_LENGTH // 2:
            # Hard split at max length
            split_pos = MAX_MESSAGE_LENGTH

        chunks.append(remaining[:split_pos])
        remaining = remaining[split_pos:].lstrip()

    return chunks


async def _send_long_message(
    update: Update, text: str, parse_mode: str = None
) -> None:
    """Send a message, splitting it if it exceeds Telegram's limit.

    Args:
        update: The Telegram update object.
        text: The message text to send.
        parse_mode: Optional parse mode (e.g., 'Markdown', 'HTML').
    """
    chunks = _split_message(text)
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=parse_mode)
        except Exception:
            # Fallback without parse_mode if formatting fails
            await update.message.reply_text(chunk)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Welcome message.

    Args:
        update: The Telegram update object.
        context: The callback context.
    """
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await update.message.reply_text(
            "Access denied. You are not authorized to use this bot."
        )
        return

    user_name = update.effective_user.first_name or "User"
    welcome_text = (
        f"Hello {user_name}! I'm J.A.R.V.I.S - Just A Rather Very Intelligent System.\n\n"
        "I'm your AI assistant with multi-agent capabilities:\n"
        "- Code generation and debugging\n"
        "- Research and analysis\n"
        "- Task management\n"
        "- Web search\n"
        "- Journal and life assistance\n\n"
        "Type /help to see available commands, or just send me a message!"
    )
    await update.message.reply_text(welcome_text)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - Show available commands.

    Args:
        update: The Telegram update object.
        context: The callback context.
    """
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await update.message.reply_text(
            "Access denied. You are not authorized to use this bot."
        )
        return

    help_text = (
        "Available Commands:\n\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/status - Show system status (providers, memory)\n"
        "/tasks - List today's tasks\n"
        "/addtask <title> - Add a new task\n"
        "/journal - Start a journal entry prompt\n"
        "/search <query> - Search the web\n\n"
        "Or just type any message and I'll process it through "
        "the appropriate AI agent!"
    )
    await update.message.reply_text(help_text)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - Show orchestrator status.

    Args:
        update: The Telegram update object.
        context: The callback context.
    """
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await update.message.reply_text(
            "Access denied. You are not authorized to use this bot."
        )
        return

    orchestrator = context.bot_data.get("orchestrator")
    if not orchestrator:
        await update.message.reply_text("System not initialized. Please try again later.")
        return

    try:
        status = orchestrator.get_status()

        # Format status information
        lines = ["J.A.R.V.I.S System Status\n"]

        # Providers
        providers = status.get("providers", {})
        lines.append("Providers:")
        for name, info in providers.items():
            available = info.get("available", False)
            status_icon = "OK" if available else "OFFLINE"
            lines.append(f"  {name}: {status_icon}")

        # Memory
        memory = status.get("memory", {})
        lines.append(f"\nMemory:")
        lines.append(f"  Messages: {memory.get('messages', 0)}/{memory.get('max_messages', 0)}")
        lines.append(f"  Has Summary: {'Yes' if memory.get('has_summary') else 'No'}")

        status_text = "\n".join(lines)
        await update.message.reply_text(status_text)

    except Exception as e:
        logger.error("Error getting status: %s", str(e))
        await update.message.reply_text(f"Error getting status: {str(e)}")


async def tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tasks command - List today's tasks.

    Args:
        update: The Telegram update object.
        context: The callback context.
    """
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await update.message.reply_text(
            "Access denied. You are not authorized to use this bot."
        )
        return

    try:
        from core.tools.scheduler_tools import get_today_tasks

        result = get_today_tasks()

        if not result.get("success"):
            await update.message.reply_text(
                f"Could not fetch tasks: {result.get('error', 'Unknown error')}"
            )
            return

        tasks = result.get("tasks", [])
        date_str = result.get("date", "today")

        if not tasks:
            await update.message.reply_text(f"No tasks scheduled for {date_str}.")
            return

        lines = [f"Tasks for {date_str}:\n"]
        for i, task in enumerate(tasks, 1):
            priority = task.get("priority", "medium")
            status = task.get("status", "pending")
            title = task.get("title", "Untitled")
            lines.append(f"{i}. [{priority.upper()}] {title} ({status})")

        await _send_long_message(update, "\n".join(lines))

    except ImportError:
        await update.message.reply_text(
            "Task system not available. Database may not be configured."
        )
    except Exception as e:
        logger.error("Error listing tasks: %s", str(e))
        await update.message.reply_text(f"Error listing tasks: {str(e)}")


async def addtask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /addtask command - Add a new task.

    Usage: /addtask <title>

    Args:
        update: The Telegram update object.
        context: The callback context.
    """
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await update.message.reply_text(
            "Access denied. You are not authorized to use this bot."
        )
        return

    # Extract task title from command arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /addtask <title>\n\nExample: /addtask Buy groceries"
        )
        return

    title = " ".join(context.args)

    try:
        from core.tools.scheduler_tools import add_task

        result = add_task(title=title)

        if result.get("success"):
            task_info = result.get("task", {})
            response = (
                f"Task added successfully!\n\n"
                f"Title: {task_info.get('title', title)}\n"
                f"Priority: {task_info.get('priority', 'medium')}\n"
                f"Status: {task_info.get('status', 'pending')}"
            )
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                f"Failed to add task: {result.get('error', 'Unknown error')}"
            )

    except ImportError:
        await update.message.reply_text(
            "Task system not available. Database may not be configured."
        )
    except Exception as e:
        logger.error("Error adding task: %s", str(e))
        await update.message.reply_text(f"Error adding task: {str(e)}")


async def journal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /journal command - Prompt for journal entry.

    Args:
        update: The Telegram update object.
        context: The callback context.
    """
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await update.message.reply_text(
            "Access denied. You are not authorized to use this bot."
        )
        return

    journal_prompt = (
        "Journal Entry Mode\n\n"
        "Write your journal entry as a message and I'll process it.\n\n"
        "Tips:\n"
        "- Describe your day, thoughts, or reflections\n"
        "- I'll help organize and store your entry\n"
        "- You can ask me to summarize past entries later\n\n"
        "Just type your journal entry now:"
    )
    await update.message.reply_text(journal_prompt)


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search command - Web search via orchestrator.

    Usage: /search <query>

    Args:
        update: The Telegram update object.
        context: The callback context.
    """
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await update.message.reply_text(
            "Access denied. You are not authorized to use this bot."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /search <query>\n\nExample: /search latest Python news"
        )
        return

    query = " ".join(context.args)
    orchestrator = context.bot_data.get("orchestrator")

    if not orchestrator:
        await update.message.reply_text("System not initialized. Please try again later.")
        return

    try:
        # Send typing indicator
        await update.message.chat.send_action("typing")

        # Process search query through orchestrator
        search_input = f"search: {query}"
        result = orchestrator.process(search_input)

        response = result.get("response", "No results found.")
        meta = f"\n\n[{result.get('provider', '?')}] {result.get('model', '?')}"

        await _send_long_message(update, response + meta)

    except Exception as e:
        logger.error("Error performing search: %s", str(e))
        await update.message.reply_text(f"Error performing search: {str(e)}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all non-command text messages.

    Routes the message through the orchestrator and returns the response.

    Args:
        update: The Telegram update object.
        context: The callback context.
    """
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await update.message.reply_text(
            "Access denied. You are not authorized to use this bot."
        )
        return

    user_text = update.message.text
    if not user_text:
        return

    orchestrator = context.bot_data.get("orchestrator")
    if not orchestrator:
        await update.message.reply_text("System not initialized. Please try again later.")
        return

    try:
        # Send typing indicator
        await update.message.chat.send_action("typing")

        # Process through orchestrator
        result = orchestrator.process(user_text)

        response = result.get("response", "I could not generate a response.")
        task_type = result.get("task_type", "unknown")
        provider = result.get("provider", "?")
        model = result.get("model", "?")

        # Add metadata footer
        meta = f"\n\n[{provider}/{model} | {task_type}]"
        full_response = response + meta

        await _send_long_message(update, full_response)

    except Exception as e:
        logger.error("Error processing message: %s", str(e))
        await update.message.reply_text(
            f"Sorry, an error occurred while processing your message: {str(e)}"
        )
