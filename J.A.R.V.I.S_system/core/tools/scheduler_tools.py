"""
Scheduler Tools - Task CRUD operations for J.A.R.V.I.S agents.

Provides task creation, listing, updating, and completion capabilities
using the DatabaseManager for MySQL/SQLite access. All operations are
safe via SQLAlchemy ORM (prevents SQL injection).
All functions return structured dict results with success/error status.

Dependencies:
    - SQLAlchemy (via core.database.db_manager)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Graceful import of database components
try:
    from core.database.db_manager import DatabaseManager
    from core.database.models import Task, SQLALCHEMY_AVAILABLE

    DB_AVAILABLE = SQLALCHEMY_AVAILABLE
except ImportError:
    DB_AVAILABLE = False
    logger.warning(
        "Database modules not available. Scheduler tools are disabled."
    )

# Singleton database manager instance
_db_manager: Optional[Any] = None


def _get_db_manager() -> Optional[Any]:
    """Get or create the singleton DatabaseManager instance.

    Returns:
        DatabaseManager instance, or None if unavailable.
    """
    global _db_manager
    if not DB_AVAILABLE:
        return None

    if _db_manager is None:
        try:
            _db_manager = DatabaseManager()
        except Exception as e:
            logger.error("Failed to initialize DatabaseManager: %s", str(e))
            return None

    return _db_manager


def add_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    category: Optional[str] = None,
    due_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new task in the database.

    Args:
        title: Task title (required).
        description: Detailed task description.
        priority: Priority level ('low', 'medium', 'high', 'urgent').
        category: Task category for organization.
        due_date: Due date in ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).

    Returns:
        Dict with 'success' and task info or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    if not title or not title.strip():
        return {"success": False, "error": "Task title cannot be empty."}

    valid_priorities = ["low", "medium", "high", "urgent"]
    if priority not in valid_priorities:
        return {
            "success": False,
            "error": "Invalid priority '{}'. Valid: {}".format(
                priority, ", ".join(valid_priorities)
            ),
        }

    db = _get_db_manager()
    if db is None or not db.is_available:
        return {
            "success": False,
            "error": "Database connection unavailable.",
        }

    session = db.get_session()
    if session is None:
        return {"success": False, "error": "Could not create database session."}

    try:
        # Parse due_date if provided
        parsed_due_date = None
        if due_date:
            try:
                # Try datetime format first
                parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    # Try date-only format
                    parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    return {
                        "success": False,
                        "error": "Invalid due_date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.",
                    }

        task = Task(
            title=title.strip(),
            description=description.strip() if description else None,
            priority=priority,
            status="pending",
            category=category.strip() if category else None,
            due_date=parsed_due_date,
        )

        session.add(task)
        session.commit()

        task_id = task.id

        return {
            "success": True,
            "task": {
                "id": task_id,
                "title": task.title,
                "priority": task.priority,
                "status": task.status,
                "category": task.category,
                "due_date": str(task.due_date) if task.due_date else None,
                "created_at": str(task.created_at),
            },
            "message": "Task '{}' created successfully.".format(title),
        }

    except Exception as e:
        session.rollback()
        logger.error("Error adding task: %s", str(e))
        return {
            "success": False,
            "error": "Failed to add task: {}".format(str(e)),
        }
    finally:
        session.close()


def list_tasks(
    status: Optional[str] = None, category: Optional[str] = None
) -> Dict[str, Any]:
    """List tasks with optional filtering by status and category.

    Args:
        status: Filter by status ('pending', 'in_progress', 'completed', 'cancelled').
        category: Filter by category name.

    Returns:
        Dict with 'success' and 'tasks' list or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    db = _get_db_manager()
    if db is None or not db.is_available:
        return {
            "success": False,
            "error": "Database connection unavailable.",
        }

    session = db.get_session()
    if session is None:
        return {"success": False, "error": "Could not create database session."}

    try:
        query = session.query(Task)

        if status:
            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            if status not in valid_statuses:
                return {
                    "success": False,
                    "error": "Invalid status '{}'. Valid: {}".format(
                        status, ", ".join(valid_statuses)
                    ),
                }
            query = query.filter(Task.status == status)

        if category:
            query = query.filter(Task.category == category)

        tasks = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()).all()

        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status,
                "category": task.category,
                "due_date": str(task.due_date) if task.due_date else None,
                "created_at": str(task.created_at),
            })

        return {
            "success": True,
            "tasks": task_list,
            "count": len(task_list),
        }

    except Exception as e:
        logger.error("Error listing tasks: %s", str(e))
        return {
            "success": False,
            "error": "Failed to list tasks: {}".format(str(e)),
        }
    finally:
        session.close()


def update_task(task_id: int, **kwargs: Any) -> Dict[str, Any]:
    """Update an existing task's fields.

    Args:
        task_id: ID of the task to update.
        **kwargs: Fields to update (title, description, priority, status,
                  category, due_date).

    Returns:
        Dict with 'success' and updated task info or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    if not task_id:
        return {"success": False, "error": "Task ID is required."}

    db = _get_db_manager()
    if db is None or not db.is_available:
        return {
            "success": False,
            "error": "Database connection unavailable.",
        }

    session = db.get_session()
    if session is None:
        return {"success": False, "error": "Could not create database session."}

    try:
        task = session.query(Task).filter(Task.id == task_id).first()

        if task is None:
            return {
                "success": False,
                "error": "Task with ID {} not found.".format(task_id),
            }

        # Allowed updatable fields
        allowed_fields = [
            "title", "description", "priority", "status", "category", "due_date"
        ]

        for key, value in kwargs.items():
            if key not in allowed_fields:
                continue

            if key == "priority" and value not in ["low", "medium", "high", "urgent"]:
                return {
                    "success": False,
                    "error": "Invalid priority: {}".format(value),
                }

            if key == "status" and value not in [
                "pending", "in_progress", "completed", "cancelled"
            ]:
                return {
                    "success": False,
                    "error": "Invalid status: {}".format(value),
                }

            if key == "due_date" and value is not None:
                try:
                    value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    try:
                        value = datetime.strptime(value, "%Y-%m-%d")
                    except (ValueError, TypeError):
                        return {
                            "success": False,
                            "error": "Invalid due_date format for update.",
                        }

            setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        session.commit()

        return {
            "success": True,
            "task": {
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "status": task.status,
                "category": task.category,
                "due_date": str(task.due_date) if task.due_date else None,
                "updated_at": str(task.updated_at),
            },
            "message": "Task {} updated successfully.".format(task_id),
        }

    except Exception as e:
        session.rollback()
        logger.error("Error updating task %s: %s", task_id, str(e))
        return {
            "success": False,
            "error": "Failed to update task: {}".format(str(e)),
        }
    finally:
        session.close()


def complete_task(task_id: int) -> Dict[str, Any]:
    """Mark a task as completed.

    Args:
        task_id: ID of the task to complete.

    Returns:
        Dict with 'success' and completion info or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    if not task_id:
        return {"success": False, "error": "Task ID is required."}

    db = _get_db_manager()
    if db is None or not db.is_available:
        return {
            "success": False,
            "error": "Database connection unavailable.",
        }

    session = db.get_session()
    if session is None:
        return {"success": False, "error": "Could not create database session."}

    try:
        task = session.query(Task).filter(Task.id == task_id).first()

        if task is None:
            return {
                "success": False,
                "error": "Task with ID {} not found.".format(task_id),
            }

        if task.status == "completed":
            return {
                "success": True,
                "message": "Task '{}' is already completed.".format(task.title),
                "task_id": task_id,
            }

        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        session.commit()

        return {
            "success": True,
            "message": "Task '{}' marked as completed.".format(task.title),
            "task": {
                "id": task.id,
                "title": task.title,
                "completed_at": str(task.completed_at),
            },
        }

    except Exception as e:
        session.rollback()
        logger.error("Error completing task %s: %s", task_id, str(e))
        return {
            "success": False,
            "error": "Failed to complete task: {}".format(str(e)),
        }
    finally:
        session.close()


def get_overdue_tasks() -> Dict[str, Any]:
    """Get all tasks that are past their due date and not yet completed.

    Returns:
        Dict with 'success' and 'tasks' list or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    db = _get_db_manager()
    if db is None or not db.is_available:
        return {
            "success": False,
            "error": "Database connection unavailable.",
        }

    session = db.get_session()
    if session is None:
        return {"success": False, "error": "Could not create database session."}

    try:
        now = datetime.utcnow()
        tasks = (
            session.query(Task)
            .filter(
                Task.due_date < now,
                Task.status.in_(["pending", "in_progress"]),
            )
            .order_by(Task.due_date.asc())
            .all()
        )

        task_list = []
        for task in tasks:
            overdue_by = now - task.due_date
            task_list.append({
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "status": task.status,
                "category": task.category,
                "due_date": str(task.due_date),
                "overdue_by": str(overdue_by),
            })

        return {
            "success": True,
            "tasks": task_list,
            "count": len(task_list),
        }

    except Exception as e:
        logger.error("Error getting overdue tasks: %s", str(e))
        return {
            "success": False,
            "error": "Failed to get overdue tasks: {}".format(str(e)),
        }
    finally:
        session.close()


def get_today_tasks() -> Dict[str, Any]:
    """Get all tasks due today.

    Returns:
        Dict with 'success' and 'tasks' list or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    db = _get_db_manager()
    if db is None or not db.is_available:
        return {
            "success": False,
            "error": "Database connection unavailable.",
        }

    session = db.get_session()
    if session is None:
        return {"success": False, "error": "Could not create database session."}

    try:
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start + timedelta(days=1)

        tasks = (
            session.query(Task)
            .filter(
                Task.due_date >= today_start,
                Task.due_date < today_end,
            )
            .order_by(Task.due_date.asc())
            .all()
        )

        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status,
                "category": task.category,
                "due_date": str(task.due_date),
            })

        return {
            "success": True,
            "tasks": task_list,
            "count": len(task_list),
            "date": str(today_start.date()),
        }

    except Exception as e:
        logger.error("Error getting today's tasks: %s", str(e))
        return {
            "success": False,
            "error": "Failed to get today's tasks: {}".format(str(e)),
        }
    finally:
        session.close()
