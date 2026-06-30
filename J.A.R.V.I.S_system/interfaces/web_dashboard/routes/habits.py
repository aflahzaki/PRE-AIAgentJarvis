"""
Habits API Routes - Habit tracking and logging.

Provides endpoints for habit management:
- GET /api/habits - List all habits with recent logs
- POST /api/habits - Create a new habit
- POST /api/habits/{id}/log - Log a habit completion
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["habits"])


class HabitCreate(BaseModel):
    """Request body for creating a habit."""

    name: str
    frequency: str = "daily"
    target_count: int = 1


class HabitLogCreate(BaseModel):
    """Request body for logging a habit completion."""

    count: int = 1
    notes: Optional[str] = None
    logged_date: Optional[str] = None


def _habit_to_dict(habit) -> dict:
    """Convert a Habit ORM object to a dictionary."""
    logs = []
    if hasattr(habit, "logs") and habit.logs:
        for log in sorted(habit.logs, key=lambda x: x.logged_date, reverse=True)[:7]:
            logs.append({
                "id": log.id,
                "logged_date": str(log.logged_date) if log.logged_date else None,
                "count": log.count,
                "notes": log.notes,
            })

    return {
        "id": habit.id,
        "name": habit.name,
        "frequency": habit.frequency,
        "target_count": habit.target_count,
        "is_active": habit.is_active,
        "created_at": str(habit.created_at) if habit.created_at else None,
        "recent_logs": logs,
    }


@router.get("/habits")
async def list_habits():
    """List all active habits with their recent logs.

    Returns:
        List of habits with last 7 days of logs.
    """
    try:
        from core.database.models import Habit
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database modules not available."
        )

    from interfaces.web_dashboard.database import get_session

    session = get_session()
    if session is None:
        raise HTTPException(
            status_code=503, detail="Database connection unavailable."
        )

    try:
        habits = (
            session.query(Habit)
            .filter(Habit.is_active == True)
            .order_by(Habit.created_at.desc())
            .all()
        )

        return {"habits": [_habit_to_dict(h) for h in habits]}
    except Exception as e:
        logger.error("Error listing habits: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error fetching habits: {}".format(str(e)),
        )
    finally:
        session.close()


@router.post("/habits")
async def create_habit(request: HabitCreate):
    """Create a new habit.

    Args:
        request: HabitCreate with habit details.

    Returns:
        Created habit object.
    """
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="Habit name is required.")

    valid_frequencies = ["daily", "weekly", "monthly"]
    if request.frequency not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail="Invalid frequency. Must be one of: {}".format(
                ", ".join(valid_frequencies)
            ),
        )

    try:
        from core.database.models import Habit
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database modules not available."
        )

    from interfaces.web_dashboard.database import get_session

    session = get_session()
    if session is None:
        raise HTTPException(
            status_code=503, detail="Database connection unavailable."
        )

    try:
        habit = Habit(
            name=request.name.strip(),
            frequency=request.frequency,
            target_count=request.target_count,
            is_active=True,
        )
        session.add(habit)
        session.commit()

        return {"success": True, "habit": _habit_to_dict(habit)}
    except Exception as e:
        session.rollback()
        logger.error("Error creating habit: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error creating habit: {}".format(str(e)),
        )
    finally:
        session.close()


@router.post("/habits/{habit_id}/log")
async def log_habit(habit_id: int, request: HabitLogCreate):
    """Log a habit completion.

    Args:
        habit_id: ID of the habit to log.
        request: HabitLogCreate with log details.

    Returns:
        Created log entry.
    """
    try:
        from core.database.models import Habit, HabitLog
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database modules not available."
        )

    from interfaces.web_dashboard.database import get_session

    session = get_session()
    if session is None:
        raise HTTPException(
            status_code=503, detail="Database connection unavailable."
        )

    try:
        habit = session.query(Habit).filter(Habit.id == habit_id).first()
        if habit is None:
            raise HTTPException(status_code=404, detail="Habit not found.")

        log_date = date.today()
        if request.logged_date:
            try:
                log_date = date.fromisoformat(request.logged_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid logged_date format. Use YYYY-MM-DD.",
                )

        habit_log = HabitLog(
            habit_id=habit_id,
            logged_date=log_date,
            count=request.count,
            notes=request.notes,
        )
        session.add(habit_log)
        session.commit()

        return {
            "success": True,
            "log": {
                "id": habit_log.id,
                "habit_id": habit_id,
                "logged_date": str(habit_log.logged_date),
                "count": habit_log.count,
                "notes": habit_log.notes,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("Error logging habit %s: %s", habit_id, str(e))
        raise HTTPException(
            status_code=500,
            detail="Error logging habit: {}".format(str(e)),
        )
    finally:
        session.close()
