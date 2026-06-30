"""
Database Manager - SQLAlchemy Connection Manager for J.A.R.V.I.S

Provides connection pooling for MySQL/MariaDB with automatic fallback
to SQLite when MySQL is unavailable. Reads configuration from environment
variables and supports auto-reconnect on connection loss.

Environment Variables:
    DB_HOST: MySQL host (default: localhost)
    DB_PORT: MySQL port (default: 3306)
    DB_USER: MySQL user (default: root)
    DB_PASSWORD: MySQL password (default: empty)
    DB_NAME: Database name (default: jarvis_db)
    DB_FALLBACK_SQLITE: Enable SQLite fallback (default: true)
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Graceful import of SQLAlchemy
try:
    from sqlalchemy import create_engine, event, text
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy.pool import QueuePool
    from sqlalchemy.exc import OperationalError, SQLAlchemyError

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning(
        "SQLAlchemy not installed. Database features are disabled. "
        "Install with: pip install sqlalchemy pymysql"
    )

# Graceful import of PyMySQL
try:
    import pymysql

    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    logger.warning(
        "PyMySQL not installed. MySQL support disabled. "
        "Install with: pip install pymysql"
    )


class DatabaseManager:
    """Manages database connections with pooling and fallback logic.

    Supports MySQL/MariaDB as primary database with automatic fallback
    to SQLite when MySQL is unavailable or DB_FALLBACK_SQLITE is enabled.

    Attributes:
        engine: SQLAlchemy engine instance (or None if unavailable).
        session_factory: Session factory for creating database sessions.
        db_type: Current database type ('mysql', 'sqlite', or None).
    """

    def __init__(self) -> None:
        """Initialize DatabaseManager and establish connection."""
        self.engine: Optional[Any] = None
        self.session_factory: Optional[Any] = None
        self.db_type: Optional[str] = None
        self._is_available: bool = False

        if not SQLALCHEMY_AVAILABLE:
            logger.error("SQLAlchemy is not available. Database disabled.")
            return

        self._connect()

    def _get_config(self) -> Dict[str, Any]:
        """Read database configuration from environment variables.

        Returns:
            Dict with database connection parameters.
        """
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "jarvis_db"),
            "fallback_sqlite": os.getenv(
                "DB_FALLBACK_SQLITE", "true"
            ).lower() in ("true", "1", "yes"),
        }

    def _connect(self) -> None:
        """Establish database connection with fallback logic.

        Attempts MySQL connection first. If it fails and fallback is
        enabled, connects to a local SQLite database instead.
        """
        config = self._get_config()

        # Try MySQL first
        if PYMYSQL_AVAILABLE:
            try:
                mysql_url = (
                    "mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
                    "?charset=utf8mb4"
                ).format(
                    user=config["user"],
                    password=config["password"],
                    host=config["host"],
                    port=config["port"],
                    database=config["database"],
                )

                self.engine = create_engine(
                    mysql_url,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    echo=False,
                )

                # Test the connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                self.db_type = "mysql"
                self._is_available = True
                self._setup_session_factory()
                self._register_events()
                logger.info(
                    "Connected to MySQL database '%s' at %s:%s",
                    config["database"],
                    config["host"],
                    config["port"],
                )
                return

            except Exception as e:
                logger.warning(
                    "MySQL connection failed: %s. %s",
                    str(e),
                    "Falling back to SQLite."
                    if config["fallback_sqlite"]
                    else "Database disabled.",
                )
                self.engine = None

        # Fallback to SQLite
        if config["fallback_sqlite"]:
            try:
                # Store SQLite DB in the project data directory
                db_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(
                        os.path.abspath(__file__)
                    ))),
                    "data",
                )
                os.makedirs(db_dir, exist_ok=True)
                sqlite_path = os.path.join(db_dir, "jarvis.db")

                sqlite_url = "sqlite:///{}".format(sqlite_path)

                self.engine = create_engine(
                    sqlite_url,
                    echo=False,
                    connect_args={"check_same_thread": False},
                )

                # Test the connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                self.db_type = "sqlite"
                self._is_available = True
                self._setup_session_factory()
                logger.info(
                    "Connected to SQLite database at %s", sqlite_path
                )
                return

            except Exception as e:
                logger.error("SQLite connection failed: %s", str(e))
                self.engine = None

        logger.error("No database connection available.")

    def _setup_session_factory(self) -> None:
        """Create the session factory bound to the current engine."""
        if self.engine is not None:
            self.session_factory = sessionmaker(bind=self.engine)

    def _register_events(self) -> None:
        """Register SQLAlchemy event listeners for auto-reconnect.

        Only applies to MySQL connections where connection drops are common.
        """
        if self.db_type != "mysql" or self.engine is None:
            return

        @event.listens_for(self.engine, "engine_connect")
        def ping_connection(connection, branch):
            """Ping connection on checkout to detect stale connections."""
            # pool_pre_ping=True handles this, but this is extra safety
            pass

    def get_session(self) -> Optional[Any]:
        """Get a new database session.

        Returns:
            SQLAlchemy Session instance, or None if database is unavailable.
        """
        if not self._is_available or self.session_factory is None:
            logger.warning("Database not available. Cannot create session.")
            return None

        try:
            return self.session_factory()
        except Exception as e:
            logger.error("Failed to create database session: %s", str(e))
            # Attempt reconnection
            self._reconnect()
            if self.session_factory is not None:
                try:
                    return self.session_factory()
                except Exception as retry_error:
                    logger.error(
                        "Session creation failed after reconnect: %s",
                        str(retry_error),
                    )
            return None

    def get_engine(self) -> Optional[Any]:
        """Get the SQLAlchemy engine instance.

        Returns:
            Engine instance, or None if database is unavailable.
        """
        return self.engine

    def _reconnect(self) -> None:
        """Attempt to reconnect to the database.

        Disposes the current engine and re-establishes the connection.
        """
        logger.info("Attempting database reconnection...")
        try:
            if self.engine is not None:
                self.engine.dispose()
        except Exception:
            pass

        self.engine = None
        self.session_factory = None
        self._is_available = False
        self._connect()

    @property
    def is_available(self) -> bool:
        """Check if the database connection is available.

        Returns:
            True if database is connected and operational.
        """
        return self._is_available

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database connection.

        Returns:
            Dict with 'success', 'db_type', and status information.
        """
        if not SQLALCHEMY_AVAILABLE:
            return {
                "success": False,
                "error": "SQLAlchemy not installed",
                "db_type": None,
            }

        if not self._is_available or self.engine is None:
            return {
                "success": False,
                "error": "No database connection",
                "db_type": None,
            }

        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {
                "success": True,
                "db_type": self.db_type,
                "url": self.engine.url.render_as_string(hide_password=True),
            }
        except Exception as e:
            # Try reconnecting
            self._reconnect()
            if self._is_available:
                return {
                    "success": True,
                    "db_type": self.db_type,
                    "url": self.engine.url.render_as_string(hide_password=True),
                    "reconnected": True,
                }
            return {
                "success": False,
                "error": "Connection lost: {}".format(str(e)),
                "db_type": self.db_type,
            }

    def close(self) -> None:
        """Close and dispose the database connection."""
        if self.engine is not None:
            try:
                self.engine.dispose()
                logger.info("Database connection closed.")
            except Exception as e:
                logger.error("Error closing database: %s", str(e))
        self._is_available = False
        self.engine = None
        self.session_factory = None
