"""
Database Migrations - Auto-create Tables for J.A.R.V.I.S

Provides idempotent table creation script that can be run multiple
times without error. Uses SQLAlchemy's create_all with checkfirst=True
(default behavior) to safely create tables.

Usage:
    # As module:
    from core.database.migrations import create_all_tables
    create_all_tables()

    # Direct execution:
    python -m core.database.migrations
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import inspect

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning(
        "SQLAlchemy not installed. Migrations are unavailable."
    )


def create_all_tables() -> Dict[str, Any]:
    """Create all database tables defined in models.py.

    This function is idempotent - it can be run multiple times safely.
    Tables that already exist will not be modified or recreated.

    Returns:
        Dict with 'success' key and details about created tables.
    """
    if not SQLALCHEMY_AVAILABLE:
        return {
            "success": False,
            "error": "SQLAlchemy not installed. Cannot create tables.",
        }

    try:
        from core.database.db_manager import DatabaseManager
        from core.database.models import Base

        # Initialize database manager (handles MySQL/SQLite fallback)
        db = DatabaseManager()

        if not db.is_available or db.engine is None:
            return {
                "success": False,
                "error": "No database connection available.",
            }

        # Get tables before creation
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        # Create all tables (idempotent - checkfirst=True is default)
        Base.metadata.create_all(db.engine)

        # Get tables after creation
        inspector = inspect(db.engine)
        all_tables = set(inspector.get_table_names())
        new_tables = all_tables - existing_tables

        # Report status
        expected_tables = [
            "tasks",
            "knowledge",
            "conversations",
            "journals",
            "habits",
            "habit_logs",
        ]

        created: List[str] = []
        already_existed: List[str] = []
        missing: List[str] = []

        for table in expected_tables:
            if table in new_tables:
                created.append(table)
                logger.info("Created table: %s", table)
            elif table in existing_tables:
                already_existed.append(table)
                logger.info("Table already exists: %s", table)
            else:
                # Check if it was created but wasn't in "new" (edge case)
                if table in all_tables:
                    already_existed.append(table)
                else:
                    missing.append(table)
                    logger.warning("Table not found after migration: %s", table)

        result = {
            "success": True,
            "db_type": db.db_type,
            "created": created,
            "already_existed": already_existed,
            "missing": missing,
            "total_tables": len(all_tables),
        }

        if created:
            print(
                "[Migrations] Created {} new table(s): {}".format(
                    len(created), ", ".join(created)
                )
            )
        if already_existed:
            print(
                "[Migrations] {} table(s) already existed: {}".format(
                    len(already_existed), ", ".join(already_existed)
                )
            )
        if not missing:
            print("[Migrations] All tables are ready.")
        else:
            print(
                "[Migrations] WARNING: Missing tables: {}".format(
                    ", ".join(missing)
                )
            )

        return result

    except Exception as e:
        error_msg = "Migration failed: {}".format(str(e))
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 50)
    print("J.A.R.V.I.S Database Migration")
    print("=" * 50)

    result = create_all_tables()

    if result["success"]:
        print("\nMigration completed successfully!")
        print("Database type: {}".format(result.get("db_type", "unknown")))
    else:
        print("\nMigration failed: {}".format(result.get("error", "Unknown error")))
