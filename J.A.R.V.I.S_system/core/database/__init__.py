"""
J.A.R.V.I.S Database Layer - MySQL/SQLite Connection Management

Provides SQLAlchemy-based ORM with connection pooling for MySQL/MariaDB
and automatic fallback to SQLite when MySQL is unavailable.

Modules:
    db_manager: Connection manager with pooling and auto-reconnect
    models: SQLAlchemy ORM table definitions (6 tables)
    migrations: Idempotent table creation script
"""

from core.database.db_manager import DatabaseManager
from core.database.models import (
    Base,
    Conversation,
    Habit,
    HabitLog,
    Journal,
    Knowledge,
    Task,
)
from core.database.migrations import create_all_tables

__all__ = [
    "DatabaseManager",
    "Base",
    "Task",
    "Knowledge",
    "Conversation",
    "Journal",
    "Habit",
    "HabitLog",
    "create_all_tables",
]
