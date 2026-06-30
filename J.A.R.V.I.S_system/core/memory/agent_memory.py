"""
Agent Memory - Per-agent persistent memory across turns and sessions.

Each agent type gets its own memory store that persists context:
- CoderAgent: remembers current_file, recent_errors, successful_fixes
- ResearcherAgent: remembers current_topic, sources_found
- SchedulerAgent: remembers recent_tasks_discussed
- WriterAgent: remembers writing_style_preference, last_draft
- LifeAssistantAgent: remembers mood_history, active_habits

Stored as JSON file per agent for persistence across sessions.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Limits to prevent unbounded growth
MAX_CONTEXT_ENTRIES = 50
MAX_RECENT_ACTIONS = 20


class AgentMemory:
    """Per-agent memory that persists context across turns.

    Provides a key-value context store and a recent actions log,
    both automatically persisted to a JSON file after each change.
    """

    def __init__(
        self,
        agent_name: str,
        storage_dir: str = "data/agent_memory",
    ) -> None:
        """Initialize agent memory.

        Args:
            agent_name: Name of the agent (used for file naming).
            storage_dir: Directory to store memory JSON files.
        """
        self.agent_name = agent_name
        self.storage_dir = storage_dir
        self.storage_path = os.path.join(storage_dir, "{}_memory.json".format(agent_name))
        self.context = {}  # type: Dict[str, Any]
        self.recent_actions = []  # type: List[Dict[str, str]]
        self._load()

    def set(self, key: str, value: Any) -> None:
        """Set a context value. Auto-saves after change.

        If the context store exceeds MAX_CONTEXT_ENTRIES, the oldest
        entries are removed to maintain the size limit.

        Args:
            key: Context key name.
            value: Value to store (must be JSON-serializable).
        """
        self.context[key] = value

        # Enforce max entries limit
        if len(self.context) > MAX_CONTEXT_ENTRIES:
            # Remove oldest entries (first inserted keys)
            keys = list(self.context.keys())
            excess = len(self.context) - MAX_CONTEXT_ENTRIES
            for k in keys[:excess]:
                del self.context[k]

        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value.

        Args:
            key: Context key to retrieve.
            default: Default value if key not found.

        Returns:
            The stored value, or default if not found.
        """
        return self.context.get(key, default)

    def append_action(self, action: str, result: str) -> None:
        """Record an action taken by the agent.

        Keeps only the last MAX_RECENT_ACTIONS entries.
        Auto-saves after change.

        Args:
            action: Action type/name (e.g., 'fixed_bug', 'read_file').
            result: Brief description of the result.
        """
        self.recent_actions.append({
            "action": action,
            "result": result,
        })

        # Enforce max recent actions limit
        if len(self.recent_actions) > MAX_RECENT_ACTIONS:
            self.recent_actions = self.recent_actions[-MAX_RECENT_ACTIONS:]

        self._save()

    def get_context_summary(self) -> str:
        """Generate a text summary of current agent context for prompt injection.

        Returns:
            Formatted string summarizing current context and recent actions,
            or empty string if no context exists.
        """
        parts = []  # type: List[str]

        if self.context:
            parts.append("Current Context:")
            for key, value in self.context.items():
                # Truncate long values for prompt injection
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                parts.append("  - {}: {}".format(key, value_str))

        if self.recent_actions:
            parts.append("Recent Actions:")
            # Show last 5 actions in summary
            for entry in self.recent_actions[-5:]:
                parts.append("  - {}: {}".format(entry["action"], entry["result"]))

        return "\n".join(parts)

    def clear(self) -> None:
        """Clear all agent memory and persist the empty state."""
        self.context = {}
        self.recent_actions = []
        self._save()

    def _save(self) -> None:
        """Persist memory to JSON file.

        Creates the storage directory if it does not exist.
        """
        try:
            os.makedirs(self.storage_dir, exist_ok=True)

            data = {
                "agent_name": self.agent_name,
                "context": self.context,
                "recent_actions": self.recent_actions,
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(
                "AgentMemory '%s': Failed to save: %s",
                self.agent_name, str(e),
            )

    def _load(self) -> None:
        """Load memory from JSON file if it exists.

        If the file does not exist or is invalid, starts with empty memory.
        """
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.context = data.get("context", {})
            self.recent_actions = data.get("recent_actions", [])

            # Enforce limits on load in case of manual edits
            if len(self.context) > MAX_CONTEXT_ENTRIES:
                keys = list(self.context.keys())
                for k in keys[:len(self.context) - MAX_CONTEXT_ENTRIES]:
                    del self.context[k]

            if len(self.recent_actions) > MAX_RECENT_ACTIONS:
                self.recent_actions = self.recent_actions[-MAX_RECENT_ACTIONS:]

            logger.debug(
                "AgentMemory '%s': Loaded %d context entries, %d actions",
                self.agent_name, len(self.context), len(self.recent_actions),
            )

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                "AgentMemory '%s': Failed to load from %s: %s. Starting fresh.",
                self.agent_name, self.storage_path, str(e),
            )
            self.context = {}
            self.recent_actions = []

    def __repr__(self) -> str:
        return "AgentMemory(agent='{}', context_keys={}, actions={})".format(
            self.agent_name,
            len(self.context),
            len(self.recent_actions),
        )
