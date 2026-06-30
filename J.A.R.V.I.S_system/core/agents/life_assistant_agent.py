"""
Life Assistant Agent - Personal life helper and wellness agent.

Inherits from BaseAgent and specializes in:
- Decision making assistance and brainstorming
- Planning and goal setting
- Health tips and motivation
- Journal/mood tracking
- Habit tracking
- General life advice that doesn't fit other agent categories

System prompt is warm, supportive, encouraging, and empathetic.
"""

import logging
from typing import Optional

from core.agents.base_agent import BaseAgent
from core.providers.base_provider import BaseProvider
from core.tools.scheduler_tools import (
    add_task,
    list_tasks,
    complete_task,
    get_today_tasks,
)
from core.tools.knowledge_tools import (
    add_knowledge,
    search_knowledge,
    get_knowledge_by_category,
    delete_knowledge,
)

logger = logging.getLogger(__name__)


LIFE_ASSISTANT_SYSTEM_PROMPT = (
    "Kamu adalah J.A.R.V.I.S Life Assistant - teman AI yang hangat, supportive, "
    "dan selalu siap membantu dalam segala aspek kehidupan.\n\n"
    "Misi Utama:\n"
    "- Membantu user membuat keputusan yang lebih baik\n"
    "- Brainstorming ide dan solusi kreatif\n"
    "- Planning dan goal setting yang realistis\n"
    "- Health tips, motivasi, dan dukungan emosional\n"
    "- Journal/mood tracking untuk self-awareness\n"
    "- Habit tracking untuk pengembangan diri\n"
    "- Menjawab pertanyaan umum yang tidak masuk kategori lain\n\n"
    "Personality:\n"
    "- Hangat: Bicara seperti teman baik yang peduli\n"
    "- Supportive: Selalu dukung dan encourage user\n"
    "- Empathetic: Pahami perasaan dan situasi user\n"
    "- Practical: Berikan saran yang bisa langsung diterapkan\n"
    "- Non-judgmental: Tidak menghakimi pilihan user\n"
    "- Motivating: Dorong user untuk terus berkembang\n\n"
    "Kemampuan:\n"
    "- Decision making: Pro/con analysis, framework keputusan\n"
    "- Brainstorming: Generate ide kreatif, mind mapping\n"
    "- Planning: Break down goals menjadi actionable steps\n"
    "- Health: Tips tidur, olahraga, nutrisi, stress management\n"
    "- Motivation: Quotes, perspective shifts, accountability\n"
    "- Journal: Catat mood, refleksi, gratitude\n"
    "- Habits: Track dan encourage positive habits\n\n"
    "Workflow:\n"
    "1. Dengarkan user dengan empati - pahami konteks emosional\n"
    "2. Tentukan jenis bantuan yang dibutuhkan\n"
    "3. Gunakan tools jika perlu (simpan ke knowledge/tasks)\n"
    "4. Berikan response yang:\n"
    "   - Acknowledge perasaan user\n"
    "   - Berikan saran practical\n"
    "   - Tawarkan follow-up atau next steps\n\n"
    "Penting:\n"
    "- Bahasa Indonesia yang santai tapi tetap respectful\n"
    "- Jangan beri saran medis profesional - arahkan ke ahli\n"
    "- Untuk mood tracking, simpan ke knowledge base\n"
    "- Untuk habits, bisa gunakan task system\n"
    "- Selalu akhiri dengan catatan positif atau encouraging"
)


class LifeAssistantAgent(BaseAgent):
    """Personal life assistant with wellness and organization tools.

    Specializes in:
    - Decision making and brainstorming
    - Planning and goal decomposition
    - Health tips and motivation
    - Journal/mood tracking (via knowledge tools)
    - Habit tracking (via scheduler tools)
    - General life advice and support
    """

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        """Initialize the Life Assistant Agent.

        Args:
            provider: LLM provider for inference.
            model: Model name to use.
            system_prompt: Optional custom system prompt.
            max_retries: Maximum self-healing retry attempts.
            temperature: Moderate-high for empathetic responses.
            max_tokens: Token limit for responses.
        """
        super().__init__(
            name="life_assistant",
            provider=provider,
            model=model,
            system_prompt=system_prompt or LIFE_ASSISTANT_SYSTEM_PROMPT,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._register_life_tools()

    def _register_life_tools(self) -> None:
        """Register life assistant tools (scheduler + knowledge)."""
        # === Scheduler tools for habit/task tracking ===

        # Tool: add_task (for habits and reminders)
        self.register_tool(
            name="add_task",
            func=add_task,
            description=(
                "Create a task, reminder, or habit entry. Use for tracking "
                "habits, setting reminders, and planning activities."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task/habit title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Details or notes",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority: low, medium, high, urgent",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (e.g., health, habit, personal, wellness)",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date (YYYY-MM-DD)",
                    },
                },
                "required": ["title"],
            },
        )

        # Tool: list_tasks
        self.register_tool(
            name="list_tasks",
            func=list_tasks,
            description=(
                "View tasks and habits. Filter by status or category "
                "to check progress on habits and goals."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter: pending, in_progress, completed, cancelled",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category",
                    },
                },
                "required": [],
            },
        )

        # Tool: complete_task
        self.register_tool(
            name="complete_task",
            func=complete_task,
            description="Mark a task or habit as completed for today.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of the task/habit to complete",
                    },
                },
                "required": ["task_id"],
            },
        )

        # Tool: get_today_tasks
        self.register_tool(
            name="get_today_tasks",
            func=get_today_tasks,
            description="See what tasks and habits are scheduled for today.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

        # === Knowledge tools for journal/mood tracking ===

        # Tool: add_knowledge (for journal entries, mood logs)
        self.register_tool(
            name="add_knowledge",
            func=add_knowledge,
            description=(
                "Save a journal entry, mood log, or personal note. "
                "Use category 'journal' for diary entries, 'mood' for "
                "mood tracking, 'goals' for aspirations."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Entry title (e.g., 'Mood Log - Happy' or 'Journal - Reflections')",
                    },
                    "content": {
                        "type": "string",
                        "description": "The journal content, mood description, or note",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category: journal, mood, goals, health, reflection",
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags (e.g., 'happy,productive,grateful')",
                    },
                },
                "required": ["title", "content"],
            },
        )

        # Tool: search_knowledge
        self.register_tool(
            name="search_knowledge",
            func=search_knowledge,
            description=(
                "Search past journal entries, mood logs, and personal notes "
                "by keyword. Helps track patterns and progress."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g., 'happy', 'stressed', 'exercise')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 10)",
                    },
                },
                "required": ["query"],
            },
        )

        # Tool: get_knowledge_by_category
        self.register_tool(
            name="get_knowledge_by_category",
            func=get_knowledge_by_category,
            description=(
                "Get all entries in a category (e.g., all mood logs, "
                "all journal entries, all goals)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category name (journal, mood, goals, health, reflection)",
                    },
                },
                "required": ["category"],
            },
        )

        # Tool: delete_knowledge
        self.register_tool(
            name="delete_knowledge",
            func=delete_knowledge,
            description="Delete a journal entry or note by ID.",
            parameters={
                "type": "object",
                "properties": {
                    "knowledge_id": {
                        "type": "integer",
                        "description": "ID of the entry to delete",
                    },
                },
                "required": ["knowledge_id"],
            },
        )

        logger.info(
            "LifeAssistantAgent: Registered %d tools", len(self._tools)
        )

    def get_agent_type(self) -> str:
        """Get the agent type identifier.

        Returns:
            'life_assistant' - identifies this as a life assistant agent.
        """
        return "life_assistant"
