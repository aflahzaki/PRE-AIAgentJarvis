"""
Shared Database Manager for Web Dashboard routes.

Provides a singleton DatabaseManager instance shared across all
web route handlers, avoiding the overhead of creating a new
DatabaseManager per request.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Shared singleton DatabaseManager instance
_db_manager: Optional[object] = None
_db_available: bool = False


def _init_db_manager():
    """Initialize the shared DatabaseManager singleton."""
    global _db_manager, _db_available
    try:
        from core.database.db_manager import DatabaseManager
        _db_manager = DatabaseManager()
        _db_available = True
        logger.info("Shared DatabaseManager initialized for web dashboard.")
    except ImportError:
        _db_manager = None
        _db_available = False
        logger.warning("Database modules not available for web dashboard.")
    except Exception as e:
        _db_manager = None
        _db_available = False
        logger.error("Failed to initialize DatabaseManager: %s", str(e))


def get_db_manager():
    """Get the shared DatabaseManager instance.

    Lazily initializes the singleton on first call.

    Returns:
        DatabaseManager instance or None if unavailable.
    """
    global _db_manager, _db_available
    if _db_manager is None and not _db_available:
        _init_db_manager()
    return _db_manager


def get_session():
    """Get a database session from the shared DatabaseManager.

    Returns:
        A SQLAlchemy session, or None if the database is unavailable.
    """
    db = get_db_manager()
    if db is None:
        return None
    try:
        return db.get_session()
    except Exception as e:
        logger.error("Failed to get database session: %s", str(e))
        return None


def is_db_available() -> bool:
    """Check if the database is available.

    Returns:
        True if DatabaseManager can be initialized, False otherwise.
    """
    global _db_available
    if _db_manager is None:
        _init_db_manager()
    return _db_available
