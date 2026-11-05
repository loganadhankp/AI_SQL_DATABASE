"""
SQLAlchemy database connectivity and engine management.
Provides:
1. Internal metadata database session factory (SQLite/MySQL).
2. Modular external target database connection manager with health checking and engine pooling.
"""

import urllib.parse
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import get_settings
from backend.database.models import Base
from backend.services.encryption import decrypt_password

settings = get_settings()

# ------------------------------------------------------------------------------
# 1. Internal Application Database (Stores users, connections, query logs)
# ------------------------------------------------------------------------------

# Handle SQLite vs MySQL for application metadata
connect_args = {}
if settings.APP_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

app_engine = create_engine(
    settings.APP_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)


def get_db():
    """FastAPI dependency yielding an internal DB session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes internal database tables on startup."""
    Base.metadata.create_all(bind=app_engine)


# ------------------------------------------------------------------------------
# 2. Dynamic Target Database Connection Manager
# ------------------------------------------------------------------------------

class DatabaseConnectionManager:
    """
    Manages connections to external user databases.
    Modular design supports MySQL today, easily extensible for PostgreSQL.
    """

    # In-memory engine cache to reuse connection pools: {connection_id: Engine}
    _engine_cache: Dict[str, Engine] = {}

    @staticmethod
    def build_url(
        host: str,
        port: int,
        database_name: str,
        username: str,
        password: str,
        dialect: str = "mysql",
    ) -> str:
        """
        Builds a safe, URL-encoded SQLAlchemy connection string.
        """
        # Safely URL-encode credentials (e.g. if password contains '@' or ':')
        safe_user = urllib.parse.quote_plus(username)
        safe_pass = urllib.parse.quote_plus(password)
        safe_db = urllib.parse.quote_plus(database_name)

        if dialect.lower() == "mysql":
            driver = "mysql+pymysql"
        elif dialect.lower() in ("postgres", "postgresql"):
            driver = "postgresql+psycopg2"
        else:
            raise ValueError(f"Unsupported database dialect: '{dialect}'")

        return f"{driver}://{safe_user}:{safe_pass}@{host}:{port}/{safe_db}"

    @classmethod
    def test_connection(
        cls,
        host: str,
        port: int,
        database_name: str,
        username: str,
        password: str,
        dialect: str = "mysql",
        timeout_seconds: int = 4,
    ) -> Dict[str, Any]:
        """
        Tests whether a database connection can be established.
        Returns a structured dictionary with success status, latency, and server version.
        """
        try:
            url = cls.build_url(host, port, database_name, username, password, dialect)
            
            # Temporary test engine with strict connect timeout
            test_engine = create_engine(
                url,
                connect_args={"connect_timeout": timeout_seconds} if dialect == "mysql" else {},
                pool_pre_ping=True,
            )

            with test_engine.connect() as conn:
                # Query server version to verify query execution capability
                version_result = conn.execute(text("SELECT VERSION();")).scalar()

            test_engine.dispose()

            return {
                "success": True,
                "message": "Connection established successfully.",
                "server_version": str(version_result),
                "dialect": dialect,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "server_version": None,
                "dialect": dialect,
            }

    @classmethod
    def get_engine_for_connection(
        cls,
        connection_id: int,
        host: str,
        port: int,
        database_name: str,
        username: str,
        encrypted_password: str,
        dialect: str = "mysql",
    ) -> Engine:
        """
        Retrieves or creates a pooled SQLAlchemy Engine for a saved connection profile.
        Decrypts password in memory only for the engine URL.
        """
        cache_key = f"{connection_id}_{host}_{port}_{database_name}_{username}"

        if cache_key in cls._engine_cache:
            return cls._engine_cache[cache_key]

        plain_password = decrypt_password(encrypted_password)
        url = cls.build_url(host, port, database_name, username, plain_password, dialect)

        engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=1800,  # Recycle connections every 30 minutes
            echo=False,
        )

        cls._engine_cache[cache_key] = engine
        return engine

    @classmethod
    def remove_engine(cls, connection_id: int):
        """Disposes and evicts an engine from the pool cache when a connection is deleted."""
        keys_to_remove = [k for k in cls._engine_cache if k.startswith(f"{connection_id}_")]
        for k in keys_to_remove:
            engine = cls._engine_cache.pop(k, None)
            if engine:
                engine.dispose()
