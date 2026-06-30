"""
Knowledge Tools - Knowledge base CRUD operations for J.A.R.V.I.S agents.

Provides knowledge storage, search, retrieval by category, and deletion
capabilities using the DatabaseManager for MySQL/SQLite access.
All operations are safe via SQLAlchemy ORM (prevents SQL injection).
All functions return structured dict results with success/error status.

Dependencies:
    - SQLAlchemy (via core.database.db_manager)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Graceful import of database components
try:
    from core.database.db_manager import DatabaseManager
    from core.database.models import Knowledge, SQLALCHEMY_AVAILABLE

    DB_AVAILABLE = SQLALCHEMY_AVAILABLE
except ImportError:
    DB_AVAILABLE = False
    logger.warning(
        "Database modules not available. Knowledge tools are disabled."
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


def add_knowledge(
    title: str,
    content: str,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a new knowledge entry to the database.

    Args:
        title: Knowledge entry title (required).
        content: Main content/body text (required).
        category: Category for organization (e.g., 'programming', 'science').
        tags: Comma-separated tags for searchability.
        source: Source URL or reference.

    Returns:
        Dict with 'success' and knowledge info or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    if not title or not title.strip():
        return {"success": False, "error": "Knowledge title cannot be empty."}

    if not content or not content.strip():
        return {"success": False, "error": "Knowledge content cannot be empty."}

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
        knowledge = Knowledge(
            title=title.strip(),
            content=content.strip(),
            category=category.strip() if category else None,
            tags=tags.strip() if tags else None,
            source=source.strip() if source else None,
        )

        session.add(knowledge)
        session.commit()

        return {
            "success": True,
            "knowledge": {
                "id": knowledge.id,
                "title": knowledge.title,
                "category": knowledge.category,
                "tags": knowledge.tags,
                "source": knowledge.source,
                "created_at": str(knowledge.created_at),
            },
            "message": "Knowledge '{}' added successfully.".format(title),
        }

    except Exception as e:
        session.rollback()
        logger.error("Error adding knowledge: %s", str(e))
        return {
            "success": False,
            "error": "Failed to add knowledge: {}".format(str(e)),
        }
    finally:
        session.close()


def search_knowledge(
    query: str, limit: int = 10
) -> Dict[str, Any]:
    """Search knowledge entries by title, content, or tags.

    Performs a case-insensitive search across title, content, and tags fields.

    Args:
        query: Search query string.
        limit: Maximum number of results to return (default: 10).

    Returns:
        Dict with 'success' and 'results' list or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    if not query or not query.strip():
        return {"success": False, "error": "Search query cannot be empty."}

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
        search_term = "%{}%".format(query.strip())

        results = (
            session.query(Knowledge)
            .filter(
                (Knowledge.title.ilike(search_term))
                | (Knowledge.content.ilike(search_term))
                | (Knowledge.tags.ilike(search_term))
            )
            .order_by(Knowledge.updated_at.desc())
            .limit(limit)
            .all()
        )

        knowledge_list = []
        for item in results:
            knowledge_list.append({
                "id": item.id,
                "title": item.title,
                "content": item.content[:200] + "..."
                if len(item.content) > 200
                else item.content,
                "category": item.category,
                "tags": item.tags,
                "source": item.source,
                "created_at": str(item.created_at),
                "updated_at": str(item.updated_at),
            })

        return {
            "success": True,
            "query": query,
            "results": knowledge_list,
            "count": len(knowledge_list),
        }

    except Exception as e:
        logger.error("Error searching knowledge: %s", str(e))
        return {
            "success": False,
            "error": "Failed to search knowledge: {}".format(str(e)),
        }
    finally:
        session.close()


def get_knowledge_by_category(category: str) -> Dict[str, Any]:
    """Get all knowledge entries in a specific category.

    Args:
        category: Category name to filter by.

    Returns:
        Dict with 'success' and 'results' list or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    if not category or not category.strip():
        return {"success": False, "error": "Category cannot be empty."}

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
        results = (
            session.query(Knowledge)
            .filter(Knowledge.category == category.strip())
            .order_by(Knowledge.created_at.desc())
            .all()
        )

        knowledge_list = []
        for item in results:
            knowledge_list.append({
                "id": item.id,
                "title": item.title,
                "content": item.content[:200] + "..."
                if len(item.content) > 200
                else item.content,
                "category": item.category,
                "tags": item.tags,
                "source": item.source,
                "created_at": str(item.created_at),
            })

        return {
            "success": True,
            "category": category,
            "results": knowledge_list,
            "count": len(knowledge_list),
        }

    except Exception as e:
        logger.error("Error getting knowledge by category: %s", str(e))
        return {
            "success": False,
            "error": "Failed to get knowledge: {}".format(str(e)),
        }
    finally:
        session.close()


def delete_knowledge(knowledge_id: int) -> Dict[str, Any]:
    """Delete a knowledge entry by ID.

    Args:
        knowledge_id: ID of the knowledge entry to delete.

    Returns:
        Dict with 'success' and deletion info or 'error'.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not available. Install SQLAlchemy.",
        }

    if not knowledge_id:
        return {"success": False, "error": "Knowledge ID is required."}

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
        knowledge = (
            session.query(Knowledge)
            .filter(Knowledge.id == knowledge_id)
            .first()
        )

        if knowledge is None:
            return {
                "success": False,
                "error": "Knowledge entry with ID {} not found.".format(
                    knowledge_id
                ),
            }

        title = knowledge.title
        session.delete(knowledge)
        session.commit()

        return {
            "success": True,
            "message": "Knowledge '{}' (ID: {}) deleted successfully.".format(
                title, knowledge_id
            ),
            "deleted_id": knowledge_id,
        }

    except Exception as e:
        session.rollback()
        logger.error("Error deleting knowledge %s: %s", knowledge_id, str(e))
        return {
            "success": False,
            "error": "Failed to delete knowledge: {}".format(str(e)),
        }
    finally:
        session.close()
