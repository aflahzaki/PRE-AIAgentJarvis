"""
Knowledge API Routes - Knowledge base management.

Provides endpoints for knowledge base operations:
- GET /api/knowledge - List all knowledge entries
- POST /api/knowledge - Add a new knowledge entry
- GET /api/knowledge/search?q=... - Search knowledge
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["knowledge"])


class KnowledgeCreate(BaseModel):
    """Request body for creating a knowledge entry."""

    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[str] = None
    source: Optional[str] = None


@router.get("/knowledge")
async def list_knowledge():
    """List all knowledge entries.

    Returns:
        List of knowledge entries ordered by creation date.
    """
    try:
        from core.database.db_manager import DatabaseManager
        from core.database.models import Knowledge
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
        entries = (
            session.query(Knowledge)
            .order_by(Knowledge.created_at.desc())
            .all()
        )

        results = []
        for item in entries:
            results.append({
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category": item.category,
                "tags": item.tags,
                "source": item.source,
                "created_at": str(item.created_at) if item.created_at else None,
                "updated_at": str(item.updated_at) if item.updated_at else None,
            })

        return {"knowledge": results, "count": len(results)}
    except Exception as e:
        logger.error("Error listing knowledge: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error fetching knowledge: {}".format(str(e)),
        )
    finally:
        session.close()


@router.get("/knowledge/search")
async def search_knowledge(
    q: str = Query(..., description="Search query"),
):
    """Search knowledge entries by title, content, or tags.

    Args:
        q: Search query string.

    Returns:
        Matching knowledge entries.
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query is required.")

    try:
        from core.tools.knowledge_tools import search_knowledge as kb_search
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Knowledge tools not available."
        )

    try:
        result = kb_search(q.strip())
        if result.get("success"):
            return {
                "results": result.get("results", []),
                "count": result.get("count", 0),
                "query": q,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Search failed."),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error searching knowledge: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error searching knowledge: {}".format(str(e)),
        )


@router.post("/knowledge")
async def create_knowledge(request: KnowledgeCreate):
    """Add a new knowledge entry.

    Args:
        request: KnowledgeCreate with entry details.

    Returns:
        Created knowledge entry info.
    """
    if not request.title or not request.title.strip():
        raise HTTPException(status_code=400, detail="Title is required.")
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=400, detail="Content is required.")

    try:
        from core.tools.knowledge_tools import add_knowledge
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Knowledge tools not available."
        )

    try:
        result = add_knowledge(
            title=request.title.strip(),
            content=request.content.strip(),
            category=request.category,
            tags=request.tags,
            source=request.source,
        )

        if result.get("success"):
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to add knowledge."),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating knowledge: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error creating knowledge: {}".format(str(e)),
        )
