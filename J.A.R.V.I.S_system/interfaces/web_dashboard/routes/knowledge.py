"""
Knowledge API Routes - Knowledge base management.

Provides endpoints for knowledge base operations:
- GET /api/knowledge - List all knowledge entries
- POST /api/knowledge - Add a new knowledge entry
- GET /api/knowledge/search?q=... - Search knowledge
- POST /api/knowledge/upload - Upload a file to the knowledge base
"""

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["knowledge"])

# Maximum upload file size: 10MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


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
        from core.database.models import Knowledge
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


@router.post("/knowledge/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form("uploaded"),
    tags: str = Form(""),
):
    """Upload a file to the knowledge base.

    Accepts a file upload, processes it through DocumentLoader,
    chunks if necessary, and stores in the knowledge base.

    Args:
        file: The uploaded file.
        category: Category for knowledge entries (default: 'uploaded').
        tags: Comma-separated tags.

    Returns:
        Upload result with entries_created count.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Check file size by reading content
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large: {:.1f}MB (max 10MB).".format(
                len(content) / (1024 * 1024)
            ),
        )

    # Check file extension
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    supported = {
        ".txt", ".md", ".pdf", ".docx", ".csv", ".json",
        ".py", ".js", ".html", ".css", ".ts", ".jsx", ".tsx",
    }
    if ext not in supported:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format '{}'. Supported: {}".format(
                ext, ", ".join(sorted(supported))
            ),
        )

    # Save to temp file for processing
    tmp_file = None
    try:
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=ext, prefix="jarvis_upload_"
        )
        tmp_file.write(content)
        tmp_file.close()

        # Process with upload_tools
        try:
            from core.tools.upload_tools import upload_to_knowledge_base
        except ImportError:
            raise HTTPException(
                status_code=503, detail="Upload tools not available."
            )

        result = upload_to_knowledge_base(
            file_path=tmp_file.name,
            category=category.strip() if category else "uploaded",
            tags=tags.strip() if tags else "",
            chunk=True,
        )

        if result.get("success"):
            return {
                "success": True,
                "filename": file.filename,
                "entries_created": result.get("entries_created", 0),
                "message": result.get("message", "Upload successful."),
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Upload processing failed."),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading file: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error processing upload: {}".format(str(e)),
        )
    finally:
        # Clean up temp file
        if tmp_file and os.path.exists(tmp_file.name):
            try:
                os.unlink(tmp_file.name)
            except OSError:
                pass
