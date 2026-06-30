"""
Tasks API Routes - Task CRUD operations.

Provides endpoints for task management:
- GET /api/tasks - List tasks with optional filters
- POST /api/tasks - Create a new task
- PUT /api/tasks/{id} - Update an existing task
- DELETE /api/tasks/{id} - Delete a task
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tasks"])


class TaskCreate(BaseModel):
    """Request body for creating a task."""

    title: str
    description: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    """Request body for updating a task."""

    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[str] = None


def _task_to_dict(task) -> dict:
    """Convert a Task ORM object to a dictionary."""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "category": task.category,
        "due_date": str(task.due_date) if task.due_date else None,
        "reminder_at": str(task.reminder_at) if task.reminder_at else None,
        "created_at": str(task.created_at) if task.created_at else None,
        "updated_at": str(task.updated_at) if task.updated_at else None,
        "completed_at": str(task.completed_at) if task.completed_at else None,
    }


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """List all tasks with optional filtering by status and category.

    Args:
        status: Optional status filter (pending, in_progress, completed, cancelled).
        category: Optional category filter.

    Returns:
        List of task objects.
    """
    try:
        from core.database.db_manager import DatabaseManager
        from core.database.models import Task
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database modules not available."
        )

    db = DatabaseManager()
    session = db.get_session()
    if session is None:
        raise HTTPException(
            status_code=503, detail="Database connection unavailable."
        )

    try:
        query = session.query(Task)

        if status:
            query = query.filter(Task.status == status)
        if category:
            query = query.filter(Task.category == category)

        query = query.order_by(Task.created_at.desc())
        tasks = query.all()

        return {"tasks": [_task_to_dict(t) for t in tasks]}
    except Exception as e:
        logger.error("Error listing tasks: %s", str(e))
        raise HTTPException(
            status_code=500, detail="Error fetching tasks: {}".format(str(e))
        )
    finally:
        session.close()


@router.post("/tasks")
async def create_task(request: TaskCreate):
    """Create a new task.

    Args:
        request: TaskCreate with task details.

    Returns:
        Created task object.
    """
    if not request.title or not request.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required.")

    try:
        from core.database.db_manager import DatabaseManager
        from core.database.models import Task
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database modules not available."
        )

    db = DatabaseManager()
    session = db.get_session()
    if session is None:
        raise HTTPException(
            status_code=503, detail="Database connection unavailable."
        )

    try:
        due_date = None
        if request.due_date:
            try:
                due_date = datetime.fromisoformat(request.due_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid due_date format. Use ISO format.",
                )

        task = Task(
            title=request.title.strip(),
            description=request.description,
            priority=request.priority,
            category=request.category,
            due_date=due_date,
        )
        session.add(task)
        session.commit()

        return {"success": True, "task": _task_to_dict(task)}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("Error creating task: %s", str(e))
        raise HTTPException(
            status_code=500, detail="Error creating task: {}".format(str(e))
        )
    finally:
        session.close()


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, request: TaskUpdate):
    """Update an existing task.

    Args:
        task_id: ID of the task to update.
        request: TaskUpdate with fields to change.

    Returns:
        Updated task object.
    """
    try:
        from core.database.db_manager import DatabaseManager
        from core.database.models import Task
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database modules not available."
        )

    db = DatabaseManager()
    session = db.get_session()
    if session is None:
        raise HTTPException(
            status_code=503, detail="Database connection unavailable."
        )

    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task is None:
            raise HTTPException(
                status_code=404, detail="Task not found."
            )

        if request.title is not None:
            task.title = request.title.strip()
        if request.description is not None:
            task.description = request.description
        if request.priority is not None:
            task.priority = request.priority
        if request.status is not None:
            task.status = request.status
            if request.status == "completed":
                task.completed_at = datetime.utcnow()
        if request.category is not None:
            task.category = request.category
        if request.due_date is not None:
            try:
                task.due_date = datetime.fromisoformat(request.due_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid due_date format. Use ISO format.",
                )

        task.updated_at = datetime.utcnow()
        session.commit()

        return {"success": True, "task": _task_to_dict(task)}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("Error updating task %s: %s", task_id, str(e))
        raise HTTPException(
            status_code=500, detail="Error updating task: {}".format(str(e))
        )
    finally:
        session.close()


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task by ID.

    Args:
        task_id: ID of the task to delete.

    Returns:
        Success confirmation.
    """
    try:
        from core.database.db_manager import DatabaseManager
        from core.database.models import Task
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database modules not available."
        )

    db = DatabaseManager()
    session = db.get_session()
    if session is None:
        raise HTTPException(
            status_code=503, detail="Database connection unavailable."
        )

    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task is None:
            raise HTTPException(
                status_code=404, detail="Task not found."
            )

        session.delete(task)
        session.commit()

        return {"success": True, "message": "Task deleted.", "deleted_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("Error deleting task %s: %s", task_id, str(e))
        raise HTTPException(
            status_code=500, detail="Error deleting task: {}".format(str(e))
        )
    finally:
        session.close()
