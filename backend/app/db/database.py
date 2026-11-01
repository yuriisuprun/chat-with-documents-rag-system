"""
Database configuration and session management.

Handles SQLAlchemy setup, engine creation, and session factories.
"""

from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.base import Base

logger = get_logger(__name__)


class Database:
    """Database management class."""

    def __init__(self, database_url: str):
        """
        Initialize database.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

    def initialize(self):
        """Initialize database engine and session factory."""
        logger.info(f"Initializing database: {self.database_url}")

        # Create engine
        self.engine = create_engine(
            self.database_url,
            echo=settings.debug,
            future=True,
        )

        # Enable foreign keys for SQLite
        if "sqlite" in self.database_url:
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,
        )

        logger.info("Database initialized successfully")

    def create_tables(self):
        """Create all tables in database."""
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self):
        """Drop all tables from database (be careful!)."""
        logger.warning("Dropping all database tables")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("Database tables dropped")

    def get_session(self) -> Session:
        """Get new database session."""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()

    @contextmanager
    def session_context(self):
        """Context manager for database sessions."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database instance
db = Database(settings.database_url)


def init_db():
    """Initialize database on application startup."""
    db.initialize()
    db.create_tables()
    logger.info("Database ready for operations")


def get_db_session() -> Session:
    """Get database session dependency for FastAPI."""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
