"""
Database Models - SQLAlchemy ORM Table Definitions for J.A.R.V.I.S

Defines 6 tables matching the project schema:
    - Task: Tasks and reminders with priority/status management
    - Knowledge: Personal knowledge base entries
    - Conversation: Chat logs for analysis and learning
    - Journal: Daily journals and notes
    - Habit: Habit definitions and tracking config
    - HabitLog: Daily habit completion logs

All models use SQLAlchemy 2.0+ declarative style with proper
type hints and relationships.
"""

import logging
from datetime import date, datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import (
        Boolean,
        Column,
        DateTime,
        Date,
        Enum,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.orm import DeclarativeBase, relationship

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning(
        "SQLAlchemy not installed. Database models are unavailable."
    )


if SQLALCHEMY_AVAILABLE:

    class Base(DeclarativeBase):
        """Base class for all J.A.R.V.I.S ORM models."""

        # Allow legacy Column() style with type annotations
        __allow_unmapped__ = True

    class Task(Base):
        """Tasks and reminders table.

        Tracks user tasks with priority levels, status, categories,
        and due dates for the scheduler agent.
        """

        __tablename__ = "tasks"

        id: int = Column(Integer, primary_key=True, autoincrement=True)
        title: str = Column(String(255), nullable=False)
        description: Optional[str] = Column(Text, nullable=True)
        priority: str = Column(
            Enum("low", "medium", "high", "urgent", name="task_priority"),
            default="medium",
            nullable=False,
        )
        status: str = Column(
            Enum(
                "pending", "in_progress", "completed", "cancelled",
                name="task_status",
            ),
            default="pending",
            nullable=False,
        )
        category: Optional[str] = Column(String(100), nullable=True)
        due_date: Optional[datetime] = Column(DateTime, nullable=True)
        reminder_at: Optional[datetime] = Column(DateTime, nullable=True)
        created_at: datetime = Column(
            DateTime, default=datetime.utcnow, nullable=False
        )
        updated_at: datetime = Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )
        completed_at: Optional[datetime] = Column(DateTime, nullable=True)

        def __repr__(self) -> str:
            return "<Task(id={}, title='{}', status='{}')>".format(
                self.id, self.title, self.status
            )

    class Knowledge(Base):
        """Knowledge base entries table.

        Stores personal knowledge items with categories and tags
        for the knowledge base search and retrieval system.
        """

        __tablename__ = "knowledge"

        id: int = Column(Integer, primary_key=True, autoincrement=True)
        title: str = Column(String(255), nullable=False)
        content: str = Column(Text, nullable=False)
        category: Optional[str] = Column(String(100), nullable=True)
        tags: Optional[str] = Column(String(500), nullable=True)
        source: Optional[str] = Column(String(255), nullable=True)
        created_at: datetime = Column(
            DateTime, default=datetime.utcnow, nullable=False
        )
        updated_at: datetime = Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )

        def __repr__(self) -> str:
            return "<Knowledge(id={}, title='{}', category='{}')>".format(
                self.id, self.title, self.category
            )

    class Conversation(Base):
        """Conversation logs table.

        Stores chat history for analysis, learning, and context.
        Tracks which agent and model handled each message.
        """

        __tablename__ = "conversations"

        id: int = Column(Integer, primary_key=True, autoincrement=True)
        session_id: str = Column(String(64), nullable=False, index=True)
        role: str = Column(
            Enum("user", "assistant", "system", name="conversation_role"),
            nullable=False,
        )
        content: str = Column(Text, nullable=False)
        agent_used: Optional[str] = Column(String(50), nullable=True)
        model_used: Optional[str] = Column(String(100), nullable=True)
        provider_used: Optional[str] = Column(String(50), nullable=True)
        tokens_used: int = Column(Integer, default=0)
        created_at: datetime = Column(
            DateTime, default=datetime.utcnow, nullable=False
        )

        def __repr__(self) -> str:
            return "<Conversation(id={}, session='{}', role='{}')>".format(
                self.id, self.session_id, self.role
            )

    class Journal(Base):
        """Daily journals and notes table.

        Stores daily reflections with mood tracking, highlights,
        challenges, and plans for the next day.
        """

        __tablename__ = "journals"

        id: int = Column(Integer, primary_key=True, autoincrement=True)
        date: date = Column(Date, nullable=False)
        mood: Optional[str] = Column(
            Enum(
                "great", "good", "neutral", "bad", "terrible",
                name="journal_mood",
            ),
            nullable=True,
        )
        content: str = Column(Text, nullable=False)
        highlights: Optional[str] = Column(Text, nullable=True)
        challenges: Optional[str] = Column(Text, nullable=True)
        tomorrow_plan: Optional[str] = Column(Text, nullable=True)
        created_at: datetime = Column(
            DateTime, default=datetime.utcnow, nullable=False
        )

        def __repr__(self) -> str:
            return "<Journal(id={}, date='{}', mood='{}')>".format(
                self.id, self.date, self.mood
            )

    class Habit(Base):
        """Habits definition table.

        Defines user habits with frequency and target tracking.
        Related to HabitLog for daily completion records.
        """

        __tablename__ = "habits"

        id: int = Column(Integer, primary_key=True, autoincrement=True)
        name: str = Column(String(255), nullable=False)
        frequency: str = Column(
            Enum("daily", "weekly", "monthly", name="habit_frequency"),
            default="daily",
            nullable=False,
        )
        target_count: int = Column(Integer, default=1)
        is_active: bool = Column(Boolean, default=True)
        created_at: datetime = Column(
            DateTime, default=datetime.utcnow, nullable=False
        )

        # Relationship to habit logs
        logs: List["HabitLog"] = relationship(
            "HabitLog", back_populates="habit", cascade="all, delete-orphan"
        )

        def __repr__(self) -> str:
            return "<Habit(id={}, name='{}', frequency='{}')>".format(
                self.id, self.name, self.frequency
            )

    class HabitLog(Base):
        """Habit completion logs table.

        Records daily habit completions linked to a parent Habit.
        Supports count tracking and optional notes.
        """

        __tablename__ = "habit_logs"

        id: int = Column(Integer, primary_key=True, autoincrement=True)
        habit_id: int = Column(
            Integer, ForeignKey("habits.id"), nullable=False
        )
        logged_date: date = Column(Date, nullable=False)
        count: int = Column(Integer, default=1)
        notes: Optional[str] = Column(Text, nullable=True)
        created_at: datetime = Column(
            DateTime, default=datetime.utcnow, nullable=False
        )

        # Relationship back to Habit
        habit: "Habit" = relationship("Habit", back_populates="logs")

        def __repr__(self) -> str:
            return "<HabitLog(id={}, habit_id={}, date='{}')>".format(
                self.id, self.habit_id, self.logged_date
            )

else:
    # Fallback: define placeholder classes when SQLAlchemy is not available
    class Base:  # type: ignore[no-redef]
        """Placeholder Base when SQLAlchemy is unavailable."""

        pass

    class Task:  # type: ignore[no-redef]
        """Placeholder Task model."""

        pass

    class Knowledge:  # type: ignore[no-redef]
        """Placeholder Knowledge model."""

        pass

    class Conversation:  # type: ignore[no-redef]
        """Placeholder Conversation model."""

        pass

    class Journal:  # type: ignore[no-redef]
        """Placeholder Journal model."""

        pass

    class Habit:  # type: ignore[no-redef]
        """Placeholder Habit model."""

        pass

    class HabitLog:  # type: ignore[no-redef]
        """Placeholder HabitLog model."""

        pass
