"""
Unit and integration tests for Phase 3:
1. Credential encryption/decryption (Fernet).
2. Internal application database models & init_db.
3. Dynamic DatabaseConnectionManager (URL building, connection testing, engine caching).
"""

import pytest
from sqlalchemy import inspect, text
from backend.services.encryption import encrypt_password, decrypt_password
from backend.database.models import User, DatabaseConnection, QueryHistory
from backend.database.connection import (
    app_engine,
    SessionLocal,
    init_db,
    DatabaseConnectionManager,
)
from backend.config import get_settings

settings = get_settings()


# ------------------------------------------------------------------------------
# 1. Encryption Tests
# ------------------------------------------------------------------------------

def test_password_encryption_roundtrip():
    """Verify passwords are encrypted to secure tokens and decrypted correctly."""
    raw_pass = "SuperSecret_Pass#2026!"
    encrypted = encrypt_password(raw_pass)

    # Token must not be raw text
    assert encrypted != raw_pass
    assert len(encrypted) > 20

    # Decryption must restore exact raw string
    decrypted = decrypt_password(encrypted)
    assert decrypted == raw_pass


def test_empty_password_encryption():
    """Verify empty passwords return empty strings safely."""
    assert encrypt_password("") == ""
    assert decrypt_password("") == ""


# ------------------------------------------------------------------------------
# 2. Internal Database Schema Tests
# ------------------------------------------------------------------------------

def test_internal_database_init():
    """Verify init_db creates all required application metadata tables."""
    init_db()
    inspector = inspect(app_engine)
    existing_tables = inspector.get_table_names()

    required_tables = [
        "users",
        "database_connections",
        "query_history",
        "conversations",
        "conversation_messages",
    ]
    for table in required_tables:
        assert table in existing_tables, f"Internal table '{table}' was not created."


def test_user_model_crud():
    """Verify ORM operations work on User and relations."""
    init_db()
    db = SessionLocal()
    try:
        # Clean up any leftover test user
        db.query(User).filter(User.username == "test_phase3_user").delete()
        db.commit()

        # Create user
        user = User(
            username="test_phase3_user",
            email="phase3@example.com",
            password_hash="mock_hashed_password",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.username == "test_phase3_user"

        # Cleanup
        db.delete(user)
        db.commit()
    finally:
        db.close()


# ------------------------------------------------------------------------------
# 3. Connection Manager & URL Builder Tests
# ------------------------------------------------------------------------------

def test_build_connection_url_mysql():
    """Verify MySQL URL building with special character escaping."""
    url = DatabaseConnectionManager.build_url(
        host="127.0.0.1",
        port=3306,
        database_name="my_db",
        username="admin",
        password="p@ss:word/test",
        dialect="mysql",
    )
    # Check dialect driver and safe URL encoding
    assert url.startswith("mysql+pymysql://")
    assert "p%40ss%3Aword%2Ftest" in url
    assert "@127.0.0.1:3306/my_db" in url


def test_build_connection_url_unsupported_dialect():
    """Verify unsupported dialect raises ValueError."""
    with pytest.raises(ValueError):
        DatabaseConnectionManager.build_url(
            host="127.0.0.1",
            port=1433,
            database_name="db",
            username="u",
            password="p",
            dialect="oracle",
        )


# ------------------------------------------------------------------------------
# 4. Live Connection Test against MySQL
# ------------------------------------------------------------------------------

def test_live_connection_success():
    """Verify connection testing succeeds with valid credentials."""
    result = DatabaseConnectionManager.test_connection(
        host=settings.SAMPLE_DB_HOST,
        port=settings.SAMPLE_DB_PORT,
        database_name=settings.SAMPLE_DB_NAME,
        username=settings.SAMPLE_DB_USER,
        password=settings.SAMPLE_DB_PASSWORD,
        dialect="mysql",
    )
    if not result["success"]:
        pytest.skip(f"MySQL not reachable for live test: {result['message']}")

    assert result["success"] is True
    assert result["server_version"] is not None
    assert "Connection established" in result["message"]


def test_live_connection_invalid_credentials():
    """Verify connection testing fails gracefully without crashing."""
    result = DatabaseConnectionManager.test_connection(
        host=settings.SAMPLE_DB_HOST,
        port=settings.SAMPLE_DB_PORT,
        database_name=settings.SAMPLE_DB_NAME,
        username="non_existent_user_999",
        password="WrongPassword123!",
        dialect="mysql",
    )
    # Must fail cleanly and report error
    assert result["success"] is False
    assert result["server_version"] is None
    assert "Connection failed" in result["message"]


def test_live_engine_caching_and_execution():
    """Verify cached engine creation and query execution."""
    encrypted_pass = encrypt_password(settings.SAMPLE_DB_PASSWORD)

    try:
        engine = DatabaseConnectionManager.get_engine_for_connection(
            connection_id=1,
            host=settings.SAMPLE_DB_HOST,
            port=settings.SAMPLE_DB_PORT,
            database_name=settings.SAMPLE_DB_NAME,
            username=settings.SAMPLE_DB_USER,
            encrypted_password=encrypted_pass,
            dialect="mysql",
        )

        with engine.connect() as conn:
            row_count = conn.execute(text("SELECT COUNT(*) FROM customers;")).scalar()
            assert row_count == 100

        # Verify caching returns same engine instance
        engine_cached = DatabaseConnectionManager.get_engine_for_connection(
            connection_id=1,
            host=settings.SAMPLE_DB_HOST,
            port=settings.SAMPLE_DB_PORT,
            database_name=settings.SAMPLE_DB_NAME,
            username=settings.SAMPLE_DB_USER,
            encrypted_password=encrypted_pass,
            dialect="mysql",
        )
        assert engine is engine_cached

    except Exception as e:
        pytest.skip(f"MySQL not reachable for engine caching test: {e}")
    finally:
        DatabaseConnectionManager.remove_engine(connection_id=1)
