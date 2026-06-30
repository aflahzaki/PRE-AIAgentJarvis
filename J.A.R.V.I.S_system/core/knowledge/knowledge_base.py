"""
Knowledge Base - CRUD + Semantic Search for J.A.R.V.I.S.

Combines DatabaseManager for persistent storage with SimpleEmbeddings
for semantic/similarity search. Supports adding, searching, retrieving,
and deleting knowledge entries.

Storage: MySQL/SQLite via DatabaseManager
Search: TF-IDF similarity via SimpleEmbeddings + keyword SQL search

Dependencies:
    - SQLAlchemy (via core.database)
    - scikit-learn (optional, for semantic search)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Graceful imports
try:
    from core.database.db_manager import DatabaseManager
    from core.database.models import Knowledge, SQLALCHEMY_AVAILABLE

    DB_AVAILABLE = SQLALCHEMY_AVAILABLE
except ImportError:
    DB_AVAILABLE = False
    logger.warning(
        "Database modules not available. KnowledgeBase storage is disabled."
    )

from core.knowledge.embeddings import SimpleEmbeddings


class KnowledgeBase:
    """Knowledge base with CRUD and semantic search capabilities.

    Uses DatabaseManager for persistent storage and SimpleEmbeddings
    for similarity-based search. Combines keyword SQL search with
    TF-IDF semantic search for better results.

    Attributes:
        db: DatabaseManager instance.
        embeddings: SimpleEmbeddings instance for similarity search.
        is_available: Whether the knowledge base is operational.
    """

    def __init__(self) -> None:
        """Initialize the knowledge base."""
        self.embeddings = SimpleEmbeddings()
        self.is_available: bool = False
        self._db: Optional[Any] = None

        if DB_AVAILABLE:
            try:
                self._db = DatabaseManager()
                if self._db.is_available:
                    self.is_available = True
                    # Create tables if needed
                    from core.database.migrations import create_all_tables
                    create_all_tables()
                    logger.info("KnowledgeBase: Initialized successfully")
                else:
                    logger.warning(
                        "KnowledgeBase: DatabaseManager not available"
                    )
            except Exception as e:
                logger.error("KnowledgeBase init error: %s", str(e))
        else:
            logger.warning(
                "KnowledgeBase: Database modules not installed"
            )

    def add(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a knowledge entry.

        Args:
            title: Entry title.
            content: Main content text.
            category: Category for organization.
            tags: Comma-separated tags.
            source: Source URL or reference.

        Returns:
            Dict with 'success' and entry info or 'error'.
        """
        if not self.is_available or self._db is None:
            return {
                "success": False,
                "error": "KnowledgeBase not available.",
            }

        if not title or not title.strip():
            return {"success": False, "error": "Title cannot be empty."}

        if not content or not content.strip():
            return {"success": False, "error": "Content cannot be empty."}

        session = self._db.get_session()
        if session is None:
            return {"success": False, "error": "Could not create session."}

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
                "message": "Knowledge '{}' added.".format(title),
            }

        except Exception as e:
            session.rollback()
            logger.error("Error adding knowledge: %s", str(e))
            return {
                "success": False,
                "error": "Failed to add: {}".format(str(e)),
            }
        finally:
            session.close()

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search knowledge using combined keyword + semantic search.

        Performs SQL LIKE search and TF-IDF similarity, then merges
        and deduplicates results.

        Args:
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            Dict with 'success' and 'results' list or 'error'.
        """
        if not self.is_available or self._db is None:
            return {
                "success": False,
                "error": "KnowledgeBase not available.",
            }

        if not query or not query.strip():
            return {"success": False, "error": "Query cannot be empty."}

        session = self._db.get_session()
        if session is None:
            return {"success": False, "error": "Could not create session."}

        try:
            # Step 1: SQL keyword search
            search_term = "%{}%".format(query.strip())
            keyword_results = (
                session.query(Knowledge)
                .filter(
                    (Knowledge.title.ilike(search_term))
                    | (Knowledge.content.ilike(search_term))
                    | (Knowledge.tags.ilike(search_term))
                )
                .order_by(Knowledge.updated_at.desc())
                .limit(limit * 2)
                .all()
            )

            # Step 2: Semantic search using embeddings
            all_entries = session.query(Knowledge).all()
            semantic_results = []

            if all_entries:
                texts = [
                    "{} {} {}".format(
                        e.title or "",
                        e.content or "",
                        e.tags or "",
                    )
                    for e in all_entries
                ]

                similar = self.embeddings.get_similar(
                    query, texts=texts, top_k=limit
                )

                for idx, score in similar:
                    if idx < len(all_entries):
                        semantic_results.append(
                            (all_entries[idx], score)
                        )

            # Step 3: Merge and deduplicate
            seen_ids = set()
            merged = []

            # Keyword results first (exact matches)
            for item in keyword_results:
                if item.id not in seen_ids:
                    seen_ids.add(item.id)
                    merged.append(self._format_entry(item, source="keyword"))

            # Then semantic results
            for item, score in semantic_results:
                if item.id not in seen_ids:
                    seen_ids.add(item.id)
                    entry = self._format_entry(item, source="semantic")
                    entry["similarity_score"] = round(score, 4)
                    merged.append(entry)

            return {
                "success": True,
                "query": query,
                "results": merged[:limit],
                "count": len(merged[:limit]),
            }

        except Exception as e:
            logger.error("Error searching knowledge: %s", str(e))
            return {
                "success": False,
                "error": "Search failed: {}".format(str(e)),
            }
        finally:
            session.close()

    def get_by_category(self, category: str) -> Dict[str, Any]:
        """Get all knowledge entries in a specific category.

        Args:
            category: Category name to filter by.

        Returns:
            Dict with 'success' and 'results' list or 'error'.
        """
        if not self.is_available or self._db is None:
            return {
                "success": False,
                "error": "KnowledgeBase not available.",
            }

        if not category or not category.strip():
            return {"success": False, "error": "Category cannot be empty."}

        session = self._db.get_session()
        if session is None:
            return {"success": False, "error": "Could not create session."}

        try:
            results = (
                session.query(Knowledge)
                .filter(Knowledge.category == category.strip())
                .order_by(Knowledge.created_at.desc())
                .all()
            )

            entries = [self._format_entry(item) for item in results]

            return {
                "success": True,
                "category": category,
                "results": entries,
                "count": len(entries),
            }

        except Exception as e:
            logger.error("Error getting by category: %s", str(e))
            return {
                "success": False,
                "error": "Failed: {}".format(str(e)),
            }
        finally:
            session.close()

    def delete(self, knowledge_id: int) -> Dict[str, Any]:
        """Delete a knowledge entry by ID.

        Args:
            knowledge_id: ID of the entry to delete.

        Returns:
            Dict with 'success' and deletion info or 'error'.
        """
        if not self.is_available or self._db is None:
            return {
                "success": False,
                "error": "KnowledgeBase not available.",
            }

        if not knowledge_id:
            return {"success": False, "error": "Knowledge ID is required."}

        session = self._db.get_session()
        if session is None:
            return {"success": False, "error": "Could not create session."}

        try:
            entry = (
                session.query(Knowledge)
                .filter(Knowledge.id == knowledge_id)
                .first()
            )

            if entry is None:
                return {
                    "success": False,
                    "error": "Entry with ID {} not found.".format(knowledge_id),
                }

            title = entry.title
            session.delete(entry)
            session.commit()

            return {
                "success": True,
                "message": "Knowledge '{}' (ID: {}) deleted.".format(
                    title, knowledge_id
                ),
                "deleted_id": knowledge_id,
            }

        except Exception as e:
            session.rollback()
            logger.error("Error deleting knowledge: %s", str(e))
            return {
                "success": False,
                "error": "Delete failed: {}".format(str(e)),
            }
        finally:
            session.close()

    @staticmethod
    def _format_entry(
        item: Any, source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a Knowledge ORM object to a dict.

        Args:
            item: Knowledge model instance.
            source: Search source ('keyword', 'semantic', or None).

        Returns:
            Formatted dict representation.
        """
        entry = {
            "id": item.id,
            "title": item.title,
            "content": item.content[:200] + "..."
            if item.content and len(item.content) > 200
            else item.content,
            "category": item.category,
            "tags": item.tags,
            "source": item.source,
            "created_at": str(item.created_at) if item.created_at else None,
            "updated_at": str(item.updated_at) if item.updated_at else None,
        }
        if source:
            entry["match_source"] = source
        return entry

    def __repr__(self) -> str:
        return "KnowledgeBase(available={}, backend='{}')".format(
            self.is_available,
            "sklearn" if self.embeddings.use_sklearn else "keyword",
        )
