"""
Conversation Memory - Persistent context across turns and sessions.

Maintains a buffer of recent messages with configurable size.
When buffer is full, older messages are summarized.
Supports save/load to JSON for persistence between sessions.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Default buffer size: 50 messages sebelum summarization
DEFAULT_MAX_MESSAGES = 50


class ConversationMemory:
    """Conversation memory with buffer management and persistence.

    Stores recent messages in a buffer. When the buffer exceeds
    max_messages, older messages are compressed into a summary.
    Supports JSON save/load for session persistence.
    """

    def __init__(self, max_messages: int = DEFAULT_MAX_MESSAGES) -> None:
        """Initialize conversation memory.

        Args:
            max_messages: Maximum messages to keep in buffer before summarizing.
        """
        self.max_messages = max_messages
        self.messages = []  # type: List[Dict[str, str]]
        self.summary = ""  # Ringkasan dari percakapan lama
        self.metadata = {}  # type: Dict[str, Union[str, int]]

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation buffer.

        Args:
            role: Message role ('system', 'user', 'assistant').
            content: Message content text.
        """
        self.messages.append({
            "role": role,
            "content": content,
        })

        # Jika buffer penuh, lakukan summarization
        if len(self.messages) > self.max_messages:
            self._summarize_old_messages()

    def get_messages(self, include_summary: bool = True) -> List[Dict[str, str]]:
        """Get all messages including optional summary context.

        Args:
            include_summary: Whether to prepend summary as system message.

        Returns:
            List of message dicts ready for LLM API call.
        """
        messages = []  # type: List[Dict[str, str]]

        # Sertakan summary sebagai context jika ada
        if include_summary and self.summary:
            messages.append({
                "role": "system",
                "content": "Previous conversation summary: {}".format(self.summary),
            })

        messages.extend(self.messages)
        return messages

    def get_last_n(self, n: int) -> List[Dict[str, str]]:
        """Get the last N messages from the buffer.

        Args:
            n: Number of recent messages to retrieve.

        Returns:
            List of the most recent N messages.
        """
        return self.messages[-n:] if n > 0 else []

    def clear(self) -> None:
        """Clear all messages and summary."""
        self.messages = []
        self.summary = ""
        self.metadata = {}
        logger.info("Conversation memory cleared")

    def _summarize_old_messages(self) -> None:
        """Summarize older messages when buffer is full.

        Keeps the last half of messages and compresses the rest into summary.
        Uses a simple text-based summarization (no AI needed).

        For tool results and code content, preserves more context (up to 500 chars)
        to avoid losing critical code snippets in multi-turn coding sessions.
        """
        # Simpan separuh terakhir, ringkas separuh pertama
        keep_count = self.max_messages // 2
        old_messages = self.messages[:-keep_count]
        self.messages = self.messages[-keep_count:]

        # Buat ringkasan sederhana dari pesan lama
        summary_parts = []
        if self.summary:
            summary_parts.append(self.summary)

        for msg in old_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "system":
                continue

            # For tool results and code, allow more context to preserve
            # critical information like file contents and error messages
            has_code_or_tool = (
                "Tool " in content
                or "[TOOL_CALL]" in content
                or "```" in content
                or "def " in content
                or "class " in content
            )
            max_len = 500 if has_code_or_tool else 200

            if len(content) > max_len:
                content = content[:max_len] + "..."

            summary_parts.append("[{}]: {}".format(role, content))

        # Keep last 30 entries (increased from 20 for longer sessions)
        self.summary = "\n".join(summary_parts[-30:])
        logger.debug(
            "Summarized %d messages. Buffer now: %d messages",
            len(old_messages),
            len(self.messages),
        )

    def save_to_file(self, file_path: str) -> Dict[str, Union[str, bool]]:
        """Save conversation to JSON file.

        Args:
            file_path: Path to save the conversation JSON.

        Returns:
            Dict with 'success' and 'path' or 'error' keys.
        """
        try:
            abs_path = os.path.abspath(file_path)
            dir_path = os.path.dirname(abs_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            data = {
                "messages": self.messages,
                "summary": self.summary,
                "metadata": self.metadata,
                "max_messages": self.max_messages,
            }

            with open(abs_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "path": abs_path,
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Error saving conversation: {}".format(str(e)),
            }

    def load_from_file(self, file_path: str) -> Dict[str, Union[str, bool]]:
        """Load conversation from JSON file.

        Args:
            file_path: Path to the conversation JSON file.

        Returns:
            Dict with 'success' or 'error' keys.
        """
        try:
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                return {
                    "success": False,
                    "error": "File not found: {}".format(file_path),
                }

            with open(abs_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.messages = data.get("messages", [])
            self.summary = data.get("summary", "")
            self.metadata = data.get("metadata", {})
            self.max_messages = data.get("max_messages", DEFAULT_MAX_MESSAGES)

            logger.info(
                "Loaded conversation: %d messages from %s",
                len(self.messages),
                file_path,
            )
            return {
                "success": True,
                "messages_loaded": len(self.messages),
            }

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": "Invalid JSON in {}: {}".format(file_path, str(e)),
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Error loading conversation: {}".format(str(e)),
            }

    @property
    def message_count(self) -> int:
        """Get the current number of messages in buffer."""
        return len(self.messages)

    @property
    def has_summary(self) -> bool:
        """Check if there is a summary from older messages."""
        return bool(self.summary)

    def __repr__(self) -> str:
        return "ConversationMemory(messages={}, max={}, has_summary={})".format(
            len(self.messages), self.max_messages, self.has_summary
        )
