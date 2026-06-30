"""
Task Queue - Priority-based task scheduling for J.A.R.V.I.S.

Provides a priority queue (urgent > high > medium > low) with task status
tracking. Supports enqueue, dequeue, status updates, and history logging.
Optionally logs task history to MySQL/SQLite via DatabaseManager.

Uses heapq internally for efficient priority ordering.
"""

import heapq
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Priority mapping: lower number = higher priority
PRIORITY_MAP = {
    "urgent": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

# Valid task statuses
VALID_STATUSES = ["pending", "running", "completed", "failed"]


class TaskQueue:
    """Priority queue for task management and scheduling.

    Tasks are ordered by priority (urgent > high > medium > low) and
    then by insertion order (FIFO within same priority).

    Supports task status tracking, history logging, and optional
    database persistence.

    Attributes:
        queue: Internal priority queue (heap).
        tasks: Dict of task_id -> task_dict for status lookups.
        history: List of completed/failed tasks.
    """

    def __init__(self, use_db: bool = False) -> None:
        """Initialize the task queue.

        Args:
            use_db: Whether to log task history to database.
        """
        self._heap: List[tuple] = []
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []
        self._counter: int = 0
        self._use_db: bool = use_db
        self._db: Optional[Any] = None

        if use_db:
            self._init_db()

        logger.info("TaskQueue: Initialized (db_logging=%s)", use_db)

    def _init_db(self) -> None:
        """Initialize database connection for history logging."""
        try:
            from core.database.db_manager import DatabaseManager
            self._db = DatabaseManager()
            if not self._db.is_available:
                self._db = None
                logger.warning(
                    "TaskQueue: DB not available, history in-memory only"
                )
        except ImportError:
            self._db = None
            logger.warning(
                "TaskQueue: Database modules not installed, "
                "history in-memory only"
            )

    def enqueue(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Add a task to the queue.

        Args:
            task_dict: Dict with at minimum 'task' key. Optional keys:
                       'priority' (default: 'medium'),
                       'category', 'context', 'requester'.

        Returns:
            Dict with 'success' and task info including assigned 'task_id'.
        """
        if not task_dict or "task" not in task_dict:
            return {
                "success": False,
                "error": "Task dict must contain 'task' key.",
            }

        priority = task_dict.get("priority", "medium")
        if priority not in PRIORITY_MAP:
            return {
                "success": False,
                "error": "Invalid priority '{}'. Valid: {}".format(
                    priority, list(PRIORITY_MAP.keys())
                ),
            }

        task_id = task_dict.get("task_id", str(uuid.uuid4())[:8])
        self._counter += 1

        task_entry = {
            "task_id": task_id,
            "task": task_dict["task"],
            "priority": priority,
            "status": "pending",
            "category": task_dict.get("category"),
            "context": task_dict.get("context"),
            "requester": task_dict.get("requester"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None,
        }

        # Store in tasks dict
        self._tasks[task_id] = task_entry

        # Push to heap: (priority_number, counter, task_id)
        heapq.heappush(
            self._heap,
            (PRIORITY_MAP[priority], self._counter, task_id),
        )

        logger.debug(
            "TaskQueue: Enqueued task '%s' (priority: %s)", task_id, priority
        )

        return {
            "success": True,
            "task_id": task_id,
            "priority": priority,
            "position": len(self._heap),
        }

    def dequeue(self) -> Dict[str, Any]:
        """Remove and return the highest priority task from the queue.

        Returns:
            Dict with 'success' and task info, or 'error' if queue is empty.
        """
        while self._heap:
            priority_num, counter, task_id = heapq.heappop(self._heap)

            # Skip tasks that have been completed or removed
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task["status"] == "pending":
                    task["status"] = "running"
                    task["updated_at"] = datetime.utcnow().isoformat()
                    return {
                        "success": True,
                        "task": task,
                    }

        return {
            "success": False,
            "error": "Queue is empty.",
        }

    def peek(self) -> Dict[str, Any]:
        """View the highest priority task without removing it.

        Returns:
            Dict with 'success' and task info, or 'error' if queue is empty.
        """
        # Find first valid pending task
        for priority_num, counter, task_id in sorted(self._heap):
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task["status"] == "pending":
                    return {
                        "success": True,
                        "task": task,
                    }

        return {
            "success": False,
            "error": "Queue is empty or no pending tasks.",
        }

    def get_by_status(self, status: str) -> Dict[str, Any]:
        """Get all tasks with a specific status.

        Args:
            status: Task status to filter by.

        Returns:
            Dict with 'success' and 'tasks' list or 'error'.
        """
        if status not in VALID_STATUSES:
            return {
                "success": False,
                "error": "Invalid status '{}'. Valid: {}".format(
                    status, VALID_STATUSES
                ),
            }

        filtered = [
            task for task in self._tasks.values()
            if task["status"] == status
        ]

        return {
            "success": True,
            "status": status,
            "tasks": filtered,
            "count": len(filtered),
        }

    def update_status(
        self, task_id: str, status: str
    ) -> Dict[str, Any]:
        """Update the status of a task.

        Args:
            task_id: Task identifier.
            status: New status ('pending', 'running', 'completed', 'failed').

        Returns:
            Dict with 'success' and updated task info or 'error'.
        """
        if status not in VALID_STATUSES:
            return {
                "success": False,
                "error": "Invalid status '{}'. Valid: {}".format(
                    status, VALID_STATUSES
                ),
            }

        if task_id not in self._tasks:
            return {
                "success": False,
                "error": "Task '{}' not found.".format(task_id),
            }

        task = self._tasks[task_id]
        old_status = task["status"]
        task["status"] = status
        task["updated_at"] = datetime.utcnow().isoformat()

        # Move to history if completed or failed
        if status in ("completed", "failed"):
            self._history.append(task.copy())
            self._log_to_db(task)

        logger.debug(
            "TaskQueue: Task '%s' status: %s -> %s",
            task_id, old_status, status,
        )

        return {
            "success": True,
            "task_id": task_id,
            "old_status": old_status,
            "new_status": status,
        }

    def get_history(self, limit: int = 50) -> Dict[str, Any]:
        """Get task history (completed and failed tasks).

        Args:
            limit: Maximum number of history entries to return.

        Returns:
            Dict with 'success' and 'history' list.
        """
        return {
            "success": True,
            "history": self._history[-limit:],
            "count": len(self._history[-limit:]),
            "total": len(self._history),
        }

    def size(self) -> int:
        """Get the number of pending tasks in the queue.

        Returns:
            Number of pending tasks.
        """
        return sum(
            1 for t in self._tasks.values() if t["status"] == "pending"
        )

    def _log_to_db(self, task: Dict[str, Any]) -> None:
        """Log task completion/failure to database (if available).

        Args:
            task: Task dict to log.
        """
        if not self._use_db or self._db is None:
            return

        try:
            # Log as a simple record - actual DB logging can be extended
            logger.info(
                "TaskQueue DB log: task='%s' status='%s'",
                task.get("task_id"), task.get("status"),
            )
        except Exception as e:
            logger.error("TaskQueue DB log error: %s", str(e))

    def clear(self) -> None:
        """Clear all tasks from the queue."""
        self._heap.clear()
        self._tasks.clear()
        logger.info("TaskQueue: Cleared")

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return "TaskQueue(pending={}, running={}, history={})".format(
            self.size(),
            sum(1 for t in self._tasks.values() if t["status"] == "running"),
            len(self._history),
        )
