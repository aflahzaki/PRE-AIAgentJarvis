"""
Telegram Bot Handlers for J.A.R.V.I.S.

Implements all command handlers, callback query handler for inline keyboards,
and the default text message handler.
Security: Only responds to users listed in TELEGRAM_ALLOWED_USERS env var.
Messages exceeding Telegram's 4096 char limit are split automatically.
Responses use HTML parse mode with proper escaping.
"""

import html
import logging
import os
import re
from typing import List, Set

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Maximum message length for Telegram
MAX_MESSAGE_LENGTH = 4096

# Cached allowed users set - parsed once at module load
_ALLOWED_USERS: Set[int] = set()


def _parse_allowed_users() -> Set[int]:
    """Parse the TELEGRAM_ALLOWED_USERS environment variable.

    TELEGRAM_ALLOWED_USERS should be a comma-separated list of user IDs.
    If not set or empty, returns an empty set (bot rejects all messages).

    Returns:
        Set of allowed user IDs as integers.
    """
    allowed_str = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
    if not allowed_str.strip():
        return set()

    user_ids: Set[int] = set()
    for uid in allowed_str.split(","):
        uid = uid.strip()
        if uid:
            try:
                user_ids.add(int(uid))
            except ValueError:
                logger.warning("Invalid user ID in TELEGRAM_ALLOWED_USERS: %s", uid)
    return user_ids


def initialize_allowed_users() -> None:
    """Initialize the cached allowed users set from environment.

    Call this once at bot startup to parse and cache the allowed user list.
    """
    global _ALLOWED_USERS
    _ALLOWED_USERS = _parse_allowed_users()
    if _ALLOWED_USERS:
        logger.info(
            "Allowed users configured: %d user(s).", len(_ALLOWED_USERS)
        )
    else:
        logger.warning(
            "TELEGRAM_ALLOWED_USERS not configured. Bot will deny all users."
        )


def _is_authorized(user_id: int) -> bool:
    """Check if a user is authorized to use the bot.

    Uses the cached allowed users set for fast lookup without
    re-parsing the environment variable on every message.

    Args:
        user_id: Telegram user ID to check.

    Returns:
        True if user is authorized, False otherwise.
    """
    if not _ALLOWED_USERS:
        # If no users configured, deny all access
        logger.warning(
            "TELEGRAM_ALLOWED_USERS not configured. Denying user %s.", user_id
        )
        return False
    return user_id in _ALLOWED_USERS


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


def format_response_html(text: str) -> str:
    """Format J.A.R.V.I.S response for Telegram HTML mode.

    - Escape HTML entities in regular text first
    - Convert markdown code blocks (```) to <code>
    - Convert inline code (`...`) to <code>
    - Convert **bold** to <b>
    - Convert *italic* to <i>
    - Truncate if over 4096 chars (leaving room for metadata)

    Args:
        text: Raw response text from the orchestrator.

    Returns:
        HTML-formatted string safe for Telegram.
    """
    if not text:
        return ""

    # First escape all HTML entities
    escaped = html.escape(text)

    # Convert markdown triple-backtick code blocks to <code>
    # Pattern: ```...``` (possibly with language hint on first line)
    escaped = re.sub(
        r'```(?:\w+)?\n?(.*?)```',
        r'<code>\1</code>',
        escaped,
        flags=re.DOTALL,
    )

    # Convert inline backtick code to <code>
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)

    # Convert **bold** to <b>
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped)

    # Convert *italic* to <i> (but not inside already-processed bold)
    escaped = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', escaped)

    # Truncate if over the limit (leave room for possible metadata)
    max_len = MAX_MESSAGE_LENGTH - 100
    if len(escaped) > max_len:
        escaped = escaped[:max_len] + "\n\n<i>[truncated]</i>"

    return escaped


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
    """Handle /tasks command - List today's tasks with inline action buttons.

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
                "Could not fetch tasks: {}".format(
                    html.escape(result.get("error", "Unknown error"))
                )
            )
            return

        tasks = result.get("tasks", [])
        date_str = result.get("date", "today")

        if not tasks:
            await update.message.reply_text(
                "<b>No tasks scheduled for {}</b>".format(html.escape(date_str)),
                parse_mode="HTML",
            )
            return

        # Send header
        await update.message.reply_text(
            "<b>Tasks for {}</b>".format(html.escape(date_str)),
            parse_mode="HTML",
        )

        # Send each task with inline keyboard buttons
        for task in tasks:
            priority = task.get("priority", "medium")
            status = task.get("status", "pending")
            title = task.get("title", "Untitled")
            task_id = task.get("id", 0)

            task_text = "<b>{}</b>\nPriority: {}\nStatus: {}".format(
                html.escape(title),
                html.escape(priority.upper()),
                html.escape(status),
            )

            # Add inline keyboard only for non-completed tasks
            if status != "completed":
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "Complete", callback_data="complete_task_{}".format(task_id)
                        ),
                        InlineKeyboardButton(
                            "Snooze", callback_data="snooze_task_{}".format(task_id)
                        ),
                    ]
                ])
                await update.message.reply_text(
                    task_text, parse_mode="HTML", reply_markup=keyboard
                )
            else:
                await update.message.reply_text(task_text, parse_mode="HTML")

    except ImportError:
        await update.message.reply_text(
            "Task system not available. Database may not be configured."
        )
    except Exception as e:
        logger.error("Error listing tasks: %s", str(e))
        await update.message.reply_text(
            "Error listing tasks: {}".format(html.escape(str(e)))
        )


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

    Routes the message through the orchestrator and returns the response
    with HTML formatting and action inline keyboards.

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

        # Format response with HTML
        formatted = format_response_html(response)

        # Add metadata footer
        meta = "\n\n<i>[{}/{} | {}]</i>".format(
            html.escape(provider), html.escape(model), html.escape(task_type)
        )
        full_response = formatted + meta

        # Add follow-up action buttons
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Follow-up", callback_data="followup"),
                InlineKeyboardButton("New Topic", callback_data="newtopic"),
            ]
        ])

        # Split and send if needed
        chunks = _split_message(full_response)
        for i, chunk in enumerate(chunks):
            try:
                # Only add keyboard to last chunk
                markup = keyboard if i == len(chunks) - 1 else None
                await update.message.reply_text(
                    chunk, parse_mode="HTML", reply_markup=markup
                )
            except Exception:
                # Fallback without HTML if formatting fails
                await update.message.reply_text(chunk)

    except Exception as e:
        logger.error("Error processing message: %s", str(e))
        await update.message.reply_text(
            "Sorry, an error occurred while processing your message. "
            "Please try again."
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboard buttons.

    Supports:
    - followup: Prompt user for a follow-up question
    - newtopic: Clear context and start fresh
    - complete_task_<id>: Mark a task as completed
    - snooze_task_<id>: Acknowledge snooze (informational)

    Args:
        update: The Telegram update object containing callback_query.
        context: The callback context.
    """
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not _is_authorized(user_id):
        await query.answer("Access denied.", show_alert=True)
        return

    data = query.data

    if data == "followup":
        # Remove the inline keyboard and prompt for follow-up
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "Send your follow-up question and I'll continue from where we left off."
        )

    elif data == "newtopic":
        # Clear context - remove keyboard and inform user
        await query.edit_message_reply_markup(reply_markup=None)
        orchestrator = context.bot_data.get("orchestrator")
        if orchestrator and hasattr(orchestrator, "memory"):
            try:
                orchestrator.memory.clear()
            except Exception:
                pass
        await query.message.reply_text(
            "Context cleared. Starting fresh - send me a new message!"
        )

    elif data.startswith("complete_task_"):
        # Mark task as completed
        try:
            task_id_str = data.split("_")[-1]
            task_id = int(task_id_str)

            from core.tools.scheduler_tools import update_task_status

            result = update_task_status(task_id=task_id, status="completed")

            if result.get("success"):
                await query.edit_message_reply_markup(reply_markup=None)
                await query.message.reply_text(
                    "Task #{} marked as completed!".format(task_id)
                )
            else:
                await query.message.reply_text(
                    "Could not complete task: {}".format(
                        result.get("error", "Unknown error")
                    )
                )
        except ImportError:
            await query.message.reply_text(
                "Task system not available."
            )
        except (ValueError, IndexError):
            await query.message.reply_text("Invalid task ID.")
        except Exception as e:
            logger.error("Error completing task via callback: %s", str(e))
            await query.message.reply_text(
                "Error completing task. Please try again."
            )

    elif data.startswith("snooze_task_"):
        # Acknowledge snooze request
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "Task snoozed. I'll remind you again later."
        )

    else:
        # Unknown callback data
        logger.warning("Unknown callback data: %s", data)
