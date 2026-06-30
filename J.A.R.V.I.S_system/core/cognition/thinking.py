"""
ThinkingEngine - Cognitive enhancement for J.A.R.V.I.S agents.

Provides:
- Chain-of-thought (CoT) prompting scaled by difficulty
- Multi-step planning for complex tasks
- Self-reflection prompts
- Error context injection from past failures
- Error logging for learning from mistakes

Difficulty levels:
- easy: No cognitive overhead (pass-through)
- medium: Brief 2-line thinking instruction
- hard: Full reasoning chain with structured thinking

Error log stored in data/cognition/error_log.json (max 100 entries).
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum entries in the error log before pruning
MAX_ERROR_LOG_ENTRIES = 100

# Path to the error log file
ERROR_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "cognition",
    "error_log.json",
)


class ThinkingEngine:
    """Cognitive enhancement engine for J.A.R.V.I.S agents.

    Adds chain-of-thought, planning, reflection, and error learning
    capabilities to agent prompts. Only ADDS to prompts, never removes
    or modifies existing content.

    Difficulty scaling:
    - easy: No overhead added
    - medium: Brief 2-line thinking prompt
    - hard: Full reasoning chain with structured approach
    """

    def __init__(self) -> None:
        """Initialize the ThinkingEngine.

        Loads error log from disk if available.
        """
        self._error_log = self._load_error_log()

    def _load_error_log(self) -> List[Dict[str, Any]]:
        """Load error log from disk.

        Returns:
            List of error log entries, or empty list if file not found.
        """
        try:
            if os.path.exists(ERROR_LOG_PATH):
                with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.debug("Could not load error log: %s", str(e))
        return []

    def _save_error_log(self) -> None:
        """Save error log to disk, pruning to MAX_ERROR_LOG_ENTRIES."""
        try:
            # Prune to max entries (keep most recent)
            if len(self._error_log) > MAX_ERROR_LOG_ENTRIES:
                self._error_log = self._error_log[-MAX_ERROR_LOG_ENTRIES:]

            # Ensure directory exists
            os.makedirs(os.path.dirname(ERROR_LOG_PATH), exist_ok=True)

            with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(self._error_log, f, ensure_ascii=False, indent=2)
        except (IOError, OSError) as e:
            logger.warning("Could not save error log: %s", str(e))

    def build_cot_prompt(self, task: str, difficulty: str) -> str:
        """Build a chain-of-thought prompt based on task and difficulty.

        Args:
            task: The task description / user input.
            difficulty: One of 'easy', 'medium', 'hard'.

        Returns:
            Chain-of-thought instruction string. Empty string for easy tasks.
        """
        if difficulty == "easy":
            return ""

        if difficulty == "medium":
            return (
                "Think step by step briefly before answering. "
                "Identify the key requirement and provide a direct solution."
            )

        # hard difficulty: full reasoning chain
        return (
            "Use structured chain-of-thought reasoning:\n"
            "1. UNDERSTAND: What exactly is being asked? Restate the problem.\n"
            "2. PLAN: What approach will you take? List the steps.\n"
            "3. EXECUTE: Implement each step carefully.\n"
            "4. VERIFY: Check your work for correctness and completeness.\n"
            "5. REFLECT: Are there edge cases or improvements to consider?"
        )

    def build_planning_prompt(self, task: str) -> str:
        """Build a multi-step planning prompt for complex tasks.

        Args:
            task: The task description.

        Returns:
            Planning instruction string.
        """
        return (
            "Before starting, create a brief plan:\n"
            "- Break the task into logical steps\n"
            "- Identify dependencies between steps\n"
            "- Note potential failure points\n"
            "- Execute steps in order, validating each before proceeding"
        )

    def build_reflection_prompt(self) -> str:
        """Build a self-reflection prompt for quality improvement.

        Returns:
            Reflection instruction string.
        """
        return (
            "After completing the task, briefly reflect:\n"
            "- Did the solution fully address the requirement?\n"
            "- Are there any assumptions that should be stated?\n"
            "- Could the approach be improved?"
        )

    def get_error_context(self, task_type: str) -> str:
        """Get relevant error context from past failures for a task type.

        Retrieves recent errors matching the given task_type to help
        the agent avoid repeating past mistakes.

        Args:
            task_type: The type of task (e.g., 'code', 'research', 'general').

        Returns:
            Error context string, or empty string if no relevant errors.
        """
        relevant_errors = [
            entry for entry in self._error_log
            if entry.get("task_type") == task_type
        ]

        if not relevant_errors:
            return ""

        # Take the 3 most recent relevant errors
        recent_errors = relevant_errors[-3:]

        lines = ["[Past errors to avoid for {} tasks]".format(task_type)]
        for entry in recent_errors:
            summary = entry.get("error_summary", "unknown error")
            context = entry.get("context", "")
            lines.append("- {}: {}".format(summary, context))
        lines.append("[End past errors]")

        return "\n".join(lines)

    def log_error(
        self, task_type: str, error_summary: str, context: str = ""
    ) -> None:
        """Log an error for future learning.

        Args:
            task_type: The type of task that failed.
            error_summary: Brief description of the error.
            context: Additional context about what was being attempted.
        """
        entry = {
            "task_type": task_type,
            "error_summary": error_summary,
            "context": context,
            "timestamp": time.time(),
        }
        self._error_log.append(entry)
        self._save_error_log()
        logger.debug(
            "ThinkingEngine: Logged error for task_type=%s: %s",
            task_type, error_summary,
        )

    def should_use_planning(self, user_input: str) -> bool:
        """Determine if a task warrants multi-step planning.

        Heuristic: tasks that are long, contain multiple requirements,
        or use planning-related keywords benefit from explicit planning.

        Args:
            user_input: The user's input text.

        Returns:
            True if planning prompt should be included.
        """
        # Long inputs likely have multiple requirements
        if len(user_input) > 200:
            return True

        # Multiple sentences suggest multi-step task
        sentences = re.split(r'[.!?\n]', user_input)
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if len(meaningful_sentences) >= 3:
            return True

        # Keywords that suggest complex multi-step work
        planning_keywords = [
            r"\b(step by step|langkah)\b",
            r"\b(then|lalu|kemudian|selanjutnya)\b",
            r"\b(first|pertama|second|kedua)\b",
            r"\b(complex|kompleks|advanced|rumit)\b",
            r"\b(multiple|beberapa|several)\b",
            r"\b(build|bangun|create|buat).*\b(and|dan)\b",
        ]

        text_lower = user_input.lower()
        for pattern in planning_keywords:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    def enhance_system_prompt(
        self,
        base_prompt: str,
        task: str,
        difficulty: str = "medium",
        task_type: str = "general",
    ) -> str:
        """Enhance a system prompt with cognitive capabilities.

        Only ADDS to the base prompt. Never removes or modifies existing content.
        For easy difficulty, returns the base prompt unchanged (no overhead).

        Args:
            base_prompt: The original system prompt to enhance.
            task: The current task / user input.
            difficulty: Task difficulty ('easy', 'medium', 'hard').
            task_type: Type of task for error context lookup.

        Returns:
            Enhanced system prompt string.
        """
        # Easy tasks: no cognitive overhead
        if difficulty == "easy":
            return base_prompt

        additions = []

        # Chain-of-thought
        cot = self.build_cot_prompt(task, difficulty)
        if cot:
            additions.append(cot)

        # Planning for complex tasks (hard difficulty or detected multi-step)
        if difficulty == "hard" and self.should_use_planning(task):
            planning = self.build_planning_prompt(task)
            additions.append(planning)

        # Reflection for hard tasks
        if difficulty == "hard":
            reflection = self.build_reflection_prompt()
            additions.append(reflection)

        # Error context from past failures
        error_context = self.get_error_context(task_type)
        if error_context:
            additions.append(error_context)

        if not additions:
            return base_prompt

        # Combine base prompt with cognitive enhancements
        enhancement_block = "\n\n[Cognitive Enhancement]\n{}\n[End Enhancement]".format(
            "\n\n".join(additions)
        )

        return base_prompt + enhancement_block
