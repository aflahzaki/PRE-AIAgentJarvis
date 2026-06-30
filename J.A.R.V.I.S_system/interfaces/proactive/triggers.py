"""
Proactive Triggers - Functions that check for conditions requiring notifications.

Each trigger function returns a list of notification message strings.
Empty list means no notification is needed.

Triggers:
    - check_overdue_tasks: Tasks past their due date
    - check_unlogged_habits: Active habits without today's log entry
    - check_upcoming_deadlines: Tasks due within the next 24 hours
    - daily_summary: Morning summary of today's tasks
    - mood_check: Afternoon reminder if no journal entry today
"""

import logging
from datetime import date, datetime, timedelta
from typing import List

logger = logging.getLogger(__name__)

# Graceful database imports
try:
    from core.database.db_manager import DatabaseManager
    from core.database.models import (
        Habit,
        HabitLog,
        Journal,
        Task,
        SQLALCHEMY_AVAILABLE,
    )
    DB_AVAILABLE = SQLALCHEMY_AVAILABLE
except ImportError:
    DB_AVAILABLE = False
    logger.warning(
        "Database modules not available. Proactive triggers are limited."
    )

# Graceful import of scheduler tools
try:
    from core.tools.scheduler_tools import get_overdue_tasks, get_today_tasks
    SCHEDULER_TOOLS_AVAILABLE = True
except ImportError:
    SCHEDULER_TOOLS_AVAILABLE = False
    logger.warning("Scheduler tools not available.")


def _get_session():
    """Get a database session, or None if unavailable."""
    if not DB_AVAILABLE:
        return None
    try:
        db = DatabaseManager()
        return db.get_session()
    except Exception as e:
        logger.error("Failed to get database session: %s", str(e))
        return None


def check_overdue_tasks() -> List[str]:
    """Check for tasks that are past their due date.

    Uses core.tools.scheduler_tools.get_overdue_tasks() to find
    overdue tasks and generates notification messages.

    Returns:
        List of notification message strings for overdue tasks.
    """
    messages: List[str] = []

    if not SCHEDULER_TOOLS_AVAILABLE:
        return messages

    try:
        result = get_overdue_tasks()
        if not result.get("success"):
            return messages

        tasks = result.get("tasks", [])
        if not tasks:
            return messages

        if len(tasks) == 1:
            task = tasks[0]
            messages.append(
                "[Overdue] Task '{}' (priority: {}) was due on {}.".format(
                    task["title"], task["priority"], task["due_date"]
                )
            )
        else:
            messages.append(
                "[Overdue] You have {} overdue tasks:".format(len(tasks))
            )
            for task in tasks[:5]:  # Limit to top 5
                messages.append(
                    "  - '{}' (priority: {}, due: {})".format(
                        task["title"], task["priority"], task["due_date"]
                    )
                )

    except Exception as e:
        logger.error("Error checking overdue tasks: %s", str(e))

    return messages


def check_unlogged_habits() -> List[str]:
    """Check for active habits that have not been logged today.

    Queries habits that are active but have no HabitLog entry
    for today's date.

    Returns:
        List of notification message strings for unlogged habits.
    """
    messages: List[str] = []

    if not DB_AVAILABLE:
        return messages

    session = _get_session()
    if session is None:
        return messages

    try:
        today = date.today()

        # Get all active habits
        active_habits = (
            session.query(Habit)
            .filter(Habit.is_active == True)  # noqa: E712
            .all()
        )

        if not active_habits:
            return messages

        # Find habits without today's log
        unlogged = []
        for habit in active_habits:
            has_log = (
                session.query(HabitLog)
                .filter(
                    HabitLog.habit_id == habit.id,
                    HabitLog.logged_date == today,
                )
                .first()
            )
            if not has_log:
                unlogged.append(habit.name)

        if unlogged:
            if len(unlogged) == 1:
                messages.append(
                    "[Habits] Don't forget to log your habit: '{}'.".format(
                        unlogged[0]
                    )
                )
            else:
                messages.append(
                    "[Habits] {} habits not logged today: {}".format(
                        len(unlogged),
                        ", ".join("'{}'".format(h) for h in unlogged[:5]),
                    )
                )

    except Exception as e:
        logger.error("Error checking unlogged habits: %s", str(e))
    finally:
        session.close()

    return messages


def check_upcoming_deadlines() -> List[str]:
    """Check for tasks due within the next 24 hours.

    Finds pending/in-progress tasks with due dates between now
    and 24 hours from now.

    Returns:
        List of notification message strings for upcoming deadlines.
    """
    messages: List[str] = []

    if not DB_AVAILABLE:
        return messages

    session = _get_session()
    if session is None:
        return messages

    try:
        now = datetime.now()
        deadline = now + timedelta(hours=24)

        upcoming_tasks = (
            session.query(Task)
            .filter(
                Task.due_date >= now,
                Task.due_date <= deadline,
                Task.status.in_(["pending", "in_progress"]),
            )
            .order_by(Task.due_date.asc())
            .all()
        )

        if not upcoming_tasks:
            return messages

        for task in upcoming_tasks[:5]:
            time_left = task.due_date - now
            hours_left = int(time_left.total_seconds() / 3600)
            messages.append(
                "[Deadline] '{}' is due in ~{} hours (priority: {}).".format(
                    task.title, hours_left, task.priority
                )
            )

    except Exception as e:
        logger.error("Error checking upcoming deadlines: %s", str(e))
    finally:
        session.close()

    return messages


def daily_summary() -> List[str]:
    """Generate a morning summary of today's tasks.

    Only triggers between 6:00 and 9:00 local time to act as a
    morning briefing. Uses get_today_tasks() from scheduler tools.

    Returns:
        List of notification message strings for the daily summary.
    """
    messages: List[str] = []

    # Only show summary in the morning window (6-9 AM)
    current_hour = datetime.now().hour
    if current_hour < 6 or current_hour >= 9:
        return messages

    if not SCHEDULER_TOOLS_AVAILABLE:
        return messages

    try:
        result = get_today_tasks()
        if not result.get("success"):
            return messages

        tasks = result.get("tasks", [])
        if not tasks:
            messages.append(
                "[Daily Summary] No tasks scheduled for today. Enjoy your free day!"
            )
        else:
            messages.append(
                "[Daily Summary] You have {} task(s) for today:".format(len(tasks))
            )
            for task in tasks[:5]:
                status_icon = (
                    "done" if task["status"] == "completed" else task["status"]
                )
                messages.append(
                    "  - '{}' [{}] (priority: {})".format(
                        task["title"], status_icon, task["priority"]
                    )
                )

    except Exception as e:
        logger.error("Error generating daily summary: %s", str(e))

    return messages


def mood_check() -> List[str]:
    """Check if a journal entry has been made today.

    Only triggers in the afternoon (14:00 - 17:00) to encourage
    daily reflection. If no journal entry exists for today, sends
    a gentle reminder.

    Returns:
        List of notification message strings for mood check reminder.
    """
    messages: List[str] = []

    # Only check in the afternoon window (2-5 PM)
    current_hour = datetime.now().hour
    if current_hour < 14 or current_hour >= 17:
        return messages

    if not DB_AVAILABLE:
        return messages

    session = _get_session()
    if session is None:
        return messages

    try:
        today = date.today()

        # Check if there's already a journal entry for today
        today_journal = (
            session.query(Journal)
            .filter(Journal.date == today)
            .first()
        )

        if not today_journal:
            messages.append(
                "[Mood Check] How's your day going? "
                "Take a moment to write a journal entry and reflect."
            )

    except Exception as e:
        logger.error("Error checking mood/journal: %s", str(e))
    finally:
        session.close()

    return messages
