"""
Automated unit and integration tests for Phase 4: Dynamic Database Schema Inspector.
Tests table extraction, column metadata, foreign key mapping, sample data previews,
and LLM schema prompt generation.
"""

import pytest
from sqlalchemy import create_engine, text
from backend.tools.schema_inspector import SchemaInspector
from backend.database.connection import DatabaseConnectionManager
from backend.services.encryption import encrypt_password
from backend.config import get_settings

settings = get_settings()


# ------------------------------------------------------------------------------
# 1. In-Memory Unit Tests (Runs without external MySQL dependencies)
# ------------------------------------------------------------------------------

@pytest.fixture
def mock_sqlite_engine():
    """Provides an in-memory SQLite database with relational foreign key tables."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        conn.execute(
            text("""
            CREATE TABLE authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                country VARCHAR(50)
            );
        """)
        )
        conn.execute(
            text("""
            CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER NOT NULL,
                title VARCHAR(150) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (author_id) REFERENCES authors(id)
            );
        """)
        )
        # Seed test data
        conn.execute(
            text("INSERT INTO authors (name, country) VALUES ('George Orwell', 'UK'), ('J.K. Rowling', 'UK');")
        )
        conn.execute(
            text("""
            INSERT INTO books (author_id, title, price) VALUES 
            (1, '1984', 19.99),
            (1, 'Animal Farm', 14.50),
            (2, 'Harry Potter', 29.99);
        """)
        )
        conn.commit()
    return engine


def test_schema_inspector_table_names(mock_sqlite_engine):
    """Verify table listing returns all tables."""
    tables = SchemaInspector.get_table_names(mock_sqlite_engine)
    assert "authors" in tables
    assert "books" in tables


def test_schema_inspector_table_metadata(mock_sqlite_engine):
    """Verify table columns, primary key, and foreign key inspection."""
    meta = SchemaInspector.get_table_metadata(mock_sqlite_engine, "books")
    assert meta.name == "books"
    assert "id" in meta.primary_keys
    assert meta.estimated_row_count == 3

    col_names = [c.name for c in meta.columns]
    assert "id" in col_names
    assert "author_id" in col_names
    assert "title" in col_names
    assert "price" in col_names

    # Check foreign keys
    assert len(meta.foreign_keys) == 1
    fk = meta.foreign_keys[0]
    assert fk.referred_table == "authors"
    assert fk.constrained_columns == ["author_id"]
    assert fk.referred_columns == ["id"]


def test_schema_inspector_table_preview(mock_sqlite_engine):
    """Verify preview limits rows and serializes data properly."""
    preview = SchemaInspector.get_table_preview(mock_sqlite_engine, "books", limit=2)
    assert preview.table_name == "books"
    assert len(preview.rows) == 2
    assert preview.columns == ["id", "author_id", "title", "price"]
    assert preview.rows[0]["title"] == "1984"


def test_format_schema_for_llm(mock_sqlite_engine):
    """Verify LLM prompt formatting generates clean readable markdown with relationships."""
    schema_text = SchemaInspector.format_schema_for_llm(mock_sqlite_engine, "library_db")
    assert "Database: library_db" in schema_text
    assert "Table: `authors`" in schema_text
    assert "Table: `books`" in schema_text
    assert "PRIMARY KEY" in schema_text
    assert "books(author_id) -> authors(id)" in schema_text

    # Test filtering by relevant tables
    filtered_text = SchemaInspector.format_schema_for_llm(
        mock_sqlite_engine, "library_db", relevant_tables=["books"]
    )
    assert "Table: `books`" in filtered_text
    assert "Table: `authors`" not in filtered_text


# ------------------------------------------------------------------------------
# 2. Live MySQL E-Commerce Database Integration Tests
# ------------------------------------------------------------------------------

def test_live_ecommerce_schema_inspection():
    """Verify inspection on the live sample e-commerce database."""
    result = DatabaseConnectionManager.test_connection(
        host=settings.SAMPLE_DB_HOST,
        port=settings.SAMPLE_DB_PORT,
        database_name=settings.SAMPLE_DB_NAME,
        username=settings.SAMPLE_DB_USER,
        password=settings.SAMPLE_DB_PASSWORD,
        dialect="mysql",
    )
    if not result["success"]:
        pytest.skip(f"Live MySQL database unreachable: {result['message']}")

    encrypted_pass = encrypt_password(settings.SAMPLE_DB_PASSWORD)
    engine = DatabaseConnectionManager.get_engine_for_connection(
        connection_id=999,
        host=settings.SAMPLE_DB_HOST,
        port=settings.SAMPLE_DB_PORT,
        database_name=settings.SAMPLE_DB_NAME,
        username=settings.SAMPLE_DB_USER,
        encrypted_password=encrypted_pass,
        dialect="mysql",
    )

    try:
        schema_meta = SchemaInspector.inspect_database(engine, settings.SAMPLE_DB_NAME)
        table_names = [t.name for t in schema_meta.tables]

        # Verify all 5 e-commerce tables
        for expected in ["customers", "products", "orders", "order_items", "payments"]:
            assert expected in table_names

        # Verify foreign keys are discovered
        orders_table = next(t for t in schema_meta.tables if t.name == "orders")
        assert any(fk.referred_table == "customers" for fk in orders_table.foreign_keys)

        # Test table preview
        cust_preview = SchemaInspector.get_table_preview(engine, "customers", limit=5)
        assert len(cust_preview.rows) == 5
        assert "email" in cust_preview.columns

        # Verify LLM prompt string contains proper dialect and relationships
        llm_schema = SchemaInspector.format_schema_for_llm(engine, settings.SAMPLE_DB_NAME)
        assert "orders(customer_id) -> customers(id)" in llm_schema
        assert "order_items(order_id) -> orders(id)" in llm_schema

    finally:
        DatabaseConnectionManager.remove_engine(999)
