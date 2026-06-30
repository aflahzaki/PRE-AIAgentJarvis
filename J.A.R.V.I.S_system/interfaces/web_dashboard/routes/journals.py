"""
Journals API Routes - Daily journal management.

Provides endpoints for journal operations:
- GET /api/journals - List all journal entries
- POST /api/journals - Create a new journal entry
"""

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["journals"])


class JournalCreate(BaseModel):
    """Request body for creating a journal entry."""

    date: Optional[str] = None
    mood: Optional[str] = None
    content: str
    highlights: Optional[str] = None
    challenges: Optional[str] = None
    tomorrow_plan: Optional[str] = None


def _journal_to_dict(journal) -> dict:
    """Convert a Journal ORM object to a dictionary."""
    return {
        "id": journal.id,
        "date": str(journal.date) if journal.date else None,
        "mood": journal.mood,
        "content": journal.content,
        "highlights": journal.highlights,
        "challenges": journal.challenges,
        "tomorrow_plan": journal.tomorrow_plan,
        "created_at": str(journal.created_at) if journal.created_at else None,
    }


@router.get("/journals")
async def list_journals():
    """List all journal entries ordered by date.

    Returns:
        List of journal entries.
    """
    try:
        from core.database.db_manager import DatabaseManager
        from core.database.models import Journal
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
        journals = (
            session.query(Journal)
            .order_by(Journal.date.desc())
            .all()
        )

        return {"journals": [_journal_to_dict(j) for j in journals]}
    except Exception as e:
        logger.error("Error listing journals: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error fetching journals: {}".format(str(e)),
        )
    finally:
        session.close()


@router.post("/journals")
async def create_journal(request: JournalCreate):
    """Create a new journal entry.

    Args:
        request: JournalCreate with journal content and metadata.

    Returns:
        Created journal entry.
    """
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=400, detail="Journal content is required.")

    valid_moods = ["great", "good", "neutral", "bad", "terrible"]
    if request.mood and request.mood not in valid_moods:
        raise HTTPException(
            status_code=400,
            detail="Invalid mood. Must be one of: {}".format(
                ", ".join(valid_moods)
            ),
        )

    try:
        from core.database.db_manager import DatabaseManager
        from core.database.models import Journal
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
        journal_date = date.today()
        if request.date:
            try:
                journal_date = date.fromisoformat(request.date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD.",
                )

        journal = Journal(
            date=journal_date,
            mood=request.mood,
            content=request.content.strip(),
            highlights=request.highlights,
            challenges=request.challenges,
            tomorrow_plan=request.tomorrow_plan,
        )
        session.add(journal)
        session.commit()

        return {"success": True, "journal": _journal_to_dict(journal)}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("Error creating journal: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error creating journal: {}".format(str(e)),
        )
    finally:
        session.close()
