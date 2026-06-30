"""
Scheduler Agent - Time management and task scheduling agent.

Inherits from BaseAgent and specializes in:
- CRUD operations for tasks and reminders
- Priority and deadline management
- Today's agenda and overdue task tracking
- Productivity tips and time management advice

System prompt focuses on productivity, time management,
and helping users stay organized.
"""

import logging
from typing import Optional

from core.agents.base_agent import BaseAgent
from core.providers.base_provider import BaseProvider
from core.tools.scheduler_tools import (
    add_task,
    list_tasks,
    update_task,
    complete_task,
    get_overdue_tasks,
    get_today_tasks,
)

logger = logging.getLogger(__name__)


# System prompt for scheduler agent - time management focused
SCHEDULER_SYSTEM_PROMPT = (
    "Kamu adalah J.A.R.V.I.S Scheduler Agent - agen manajemen waktu dan "
    "produktivitas yang membantu user mengatur kehidupannya.\n\n"
    "Misi Utama:\n"
    "- Mengelola tasks, reminders, dan deadlines user\n"
    "- Membantu user prioritaskan pekerjaan (urgent/high/medium/low)\n"
    "- Mengingatkan tentang tasks yang overdue\n"
    "- Memberikan overview agenda hari ini\n"
    "- Tips produktivitas yang practical\n\n"
    "Personality:\n"
    "- Terorganisir: Selalu strukturkan informasi dengan jelas\n"
    "- Proaktif: Ingatkan user tentang deadlines yang mendekat\n"
    "- Motivating: Dorong user untuk menyelesaikan tasks\n"
    "- Realistis: Bantu user set prioritas yang masuk akal\n\n"
    "Workflow:\n"
    "1. Pahami apa yang user inginkan (tambah task, lihat jadwal, dll)\n"
    "2. Gunakan tools yang sesuai:\n"
    "   - add_task: untuk membuat task baru\n"
    "   - list_tasks: untuk melihat daftar tasks\n"
    "   - update_task: untuk mengubah task existing\n"
    "   - complete_task: untuk menandai task selesai\n"
    "   - get_overdue_tasks: untuk cek yang terlambat\n"
    "   - get_today_tasks: untuk agenda hari ini\n"
    "3. Berikan response yang terstruktur:\n"
    "   - Konfirmasi aksi yang dilakukan\n"
    "   - Summary status tasks\n"
    "   - Saran produktivitas jika relevan\n\n"
    "Format response:\n"
    "- Gunakan emoji untuk status: done, pending, overdue\n"
    "- Tampilkan deadline dalam format yang mudah dibaca\n"
    "- Prioritas: URGENT > HIGH > MEDIUM > LOW\n"
    "- Bahasa Indonesia sebagai default"
)


class SchedulerAgent(BaseAgent):
    """Time management agent with task scheduling capabilities.

    Specializes in:
    - Creating and managing tasks with deadlines
    - Priority-based task organization
    - Daily agenda management
    - Overdue task tracking and reminders
    - Productivity advice
    """

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 5,
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> None:
        """Initialize the Scheduler Agent.

        Args:
            provider: LLM provider for inference.
            model: Model name to use.
            system_prompt: Optional custom system prompt.
            max_retries: Maximum self-healing retry attempts.
            temperature: Moderate temperature for balanced responses.
            max_tokens: Token limit for responses.
        """
        super().__init__(
            name="scheduler",
            provider=provider,
            model=model,
            system_prompt=system_prompt or SCHEDULER_SYSTEM_PROMPT,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._register_scheduler_tools()

    def _register_scheduler_tools(self) -> None:
        """Register scheduler/task management tools."""
        # Tool: add_task
        self.register_tool(
            name="add_task",
            func=add_task,
            description=(
                "Create a new task with title, description, priority, "
                "category, and optional due date."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title (required)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed task description",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority level: low, medium, high, urgent (default: medium)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Task category (e.g., work, personal, study)",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format",
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
                "List tasks with optional filtering by status and/or category."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: pending, in_progress, completed, cancelled",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category name",
                    },
                },
                "required": [],
            },
        )

        # Tool: update_task
        self.register_tool(
            name="update_task",
            func=update_task,
            description=(
                "Update an existing task. Can change title, description, "
                "priority, status, category, or due_date."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of the task to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "New task title",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description",
                    },
                    "priority": {
                        "type": "string",
                        "description": "New priority: low, medium, high, urgent",
                    },
                    "status": {
                        "type": "string",
                        "description": "New status: pending, in_progress, completed, cancelled",
                    },
                    "category": {
                        "type": "string",
                        "description": "New category",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "New due date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
                    },
                },
                "required": ["task_id"],
            },
        )

        # Tool: complete_task
        self.register_tool(
            name="complete_task",
            func=complete_task,
            description="Mark a task as completed by its ID.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of the task to mark as completed",
                    },
                },
                "required": ["task_id"],
            },
        )

        # Tool: get_overdue_tasks
        self.register_tool(
            name="get_overdue_tasks",
            func=get_overdue_tasks,
            description=(
                "Get all tasks that are past their due date and not yet completed."
            ),
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

        # Tool: get_today_tasks
        self.register_tool(
            name="get_today_tasks",
            func=get_today_tasks,
            description="Get all tasks that are due today.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

        logger.info("SchedulerAgent: Registered %d tools", len(self._tools))

    def get_agent_type(self) -> str:
        """Get the agent type identifier.

        Returns:
            'scheduler' - identifies this as a scheduling agent.
        """
        return "scheduler"
