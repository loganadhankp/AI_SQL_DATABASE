"""
Tests for Phase 6: AST-Based SQL Validation & Safe Execution.
Tests security filter against destructive statements, stacked queries, and verifies execution engine.
"""

import pytest
from sqlalchemy import create_engine, text
from backend.tools.sql_validator import SQLValidator
from backend.tools.database_executor import DatabaseExecutor


# ------------------------------------------------------------------------------
# 1. SQL Validator Security Rejection Tests
# ------------------------------------------------------------------------------

def test_validator_accepts_clean_select():
    """Verify clean SELECT statements pass validation."""
    query = "SELECT id, name, email FROM customers WHERE city = 'New York' ORDER BY id ASC LIMIT 10"
    is_valid, msg, sanitized = SQLValidator.validate_sql(query, dialect="mysql")
    assert is_valid is True
    assert "LIMIT 10" in sanitized or "limit 10" in sanitized.lower()


def test_validator_enforces_limit_when_missing():
    """Verify LIMIT clause is added if omitted."""
    query = "SELECT * FROM products"
    is_valid, msg, sanitized = SQLValidator.validate_sql(query, dialect="mysql", max_allowed_rows=500)
    assert is_valid is True
    assert "LIMIT 500" in sanitized


def test_validator_caps_excessive_limit():
    """Verify excessive limits are reduced to max_allowed_rows."""
    query = "SELECT * FROM orders LIMIT 50000"
    is_valid, msg, sanitized = SQLValidator.validate_sql(query, dialect="mysql", max_allowed_rows=1000)
    assert is_valid is True
    assert "50000" not in sanitized
    assert "LIMIT 1000" in sanitized


def test_validator_rejects_drop():
    """Security check: Reject DROP TABLE."""
    query = "DROP TABLE customers"
    is_valid, msg, sanitized = SQLValidator.validate_sql(query)
    assert is_valid is False
    assert "Security Violation" in msg


def test_validator_rejects_delete():
    """Security check: Reject DELETE."""
    query = "DELETE FROM orders WHERE id = 1"
    is_valid, msg, sanitized = SQLValidator.validate_sql(query)
    assert is_valid is False
    assert "Security Violation" in msg


def test_validator_rejects_insert_and_update():
    """Security check: Reject INSERT and UPDATE."""
    is_valid_ins, _, _ = SQLValidator.validate_sql("INSERT INTO customers (name) VALUES ('Hacker')")
    assert is_valid_ins is False

    is_valid_upd, _, _ = SQLValidator.validate_sql("UPDATE products SET price = 0")
    assert is_valid_upd is False


def test_validator_rejects_alter_and_truncate():
    """Security check: Reject ALTER and TRUNCATE."""
    assert SQLValidator.validate_sql("ALTER TABLE customers ADD COLUMN hack VARCHAR(10)")[0] is False
    assert SQLValidator.validate_sql("TRUNCATE TABLE payments")[0] is False


def test_validator_rejects_stacked_queries():
    """Security check: Reject stacked SQL injection statements."""
    query = "SELECT * FROM customers; DROP TABLE orders;"
    is_valid, msg, _ = SQLValidator.validate_sql(query)
    assert is_valid is False
    assert "Stacked queries" in msg


def test_validator_rejects_grant_revoke():
    """Security check: Reject permission alterations."""
    assert SQLValidator.validate_sql("GRANT ALL PRIVILEGES ON *.* TO 'hacker'@'%'")[0] is False
    assert SQLValidator.validate_sql("REVOKE ALL PRIVILEGES ON *.* FROM 'root'@'%'")[0] is False


# ------------------------------------------------------------------------------
# 2. Database Executor Tests (In-Memory Engine)
# ------------------------------------------------------------------------------

@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE items (id INT, name TEXT, price REAL);"))
        conn.execute(text("INSERT INTO items VALUES (1, 'Widget', 19.99), (2, 'Gadget', 49.50);"))
        conn.commit()
    return engine


def test_executor_successful_query(memory_db):
    """Verify successful execution returns rows, columns, and latency."""
    res = DatabaseExecutor.execute_query(memory_db, "SELECT * FROM items ORDER BY id ASC")
    assert res.success is True
    assert res.row_count == 2
    assert res.columns == ["id", "name", "price"]
    assert res.rows[0]["name"] == "Widget"
    assert res.execution_time_ms > 0


def test_executor_handles_schema_error(memory_db):
    """Verify execution of invalid column produces classified error."""
    res = DatabaseExecutor.execute_query(memory_db, "SELECT non_existent_column FROM items")
    assert res.success is False
    assert res.row_count == 0
    assert res.error_category in ("schema", "syntax")
    assert res.error_message is not None
