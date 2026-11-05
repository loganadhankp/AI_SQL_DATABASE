"""
Automated unit and integration tests for Phase 5:
Gemini API integration, Question Understanding, and Natural-Language-to-SQL Generation.
"""

import pytest
from backend.agents.question_analyzer import analyze_question, _fallback_analyze
from backend.agents.sql_generator import clean_sql_query, generate_sql
from backend.schemas.query_generation import SQLGenerationResult
from backend.config import get_settings

settings = get_settings()

MOCK_SCHEMA = """
Database: ecommerce_db (Dialect: MYSQL)
Schema Overview:
Table: `customers` (approx 100 rows)
  - `id`: INTEGER [PRIMARY KEY, NOT NULL]
  - `name`: VARCHAR(100) [NOT NULL]
  - `email`: VARCHAR(150) [NOT NULL]
  - `city`: VARCHAR(80) [NOT NULL]
  - `created_at`: DATETIME [NOT NULL]

Table: `products` (approx 35 rows)
  - `id`: INTEGER [PRIMARY KEY, NOT NULL]
  - `name`: VARCHAR(150) [NOT NULL]
  - `category`: VARCHAR(80) [NOT NULL]
  - `price`: DECIMAL(10, 2) [NOT NULL]
  - `stock`: INTEGER [NOT NULL]

Table: `orders` (approx 220 rows)
  - `id`: INTEGER [PRIMARY KEY, NOT NULL]
  - `customer_id`: INTEGER [NOT NULL]
  - `order_date`: DATETIME [NOT NULL]
  - `status`: VARCHAR(20) [NOT NULL]
  - FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`)

Table: `order_items` (approx 399 rows)
  - `id`: INTEGER [PRIMARY KEY, NOT NULL]
  - `order_id`: INTEGER [NOT NULL]
  - `product_id`: INTEGER [NOT NULL]
  - `quantity`: INTEGER [NOT NULL]
  - `price`: DECIMAL(10, 2) [NOT NULL]
  - FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`)
  - FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)

Key Relationships (Foreign Keys for JOINs):
  • orders(customer_id) -> customers(id)
  • order_items(order_id) -> orders(id)
  • order_items(product_id) -> products(id)
"""


# ------------------------------------------------------------------------------
# 1. SQL Cleaning Utility Tests
# ------------------------------------------------------------------------------

def test_clean_sql_query():
    """Verify markdown fences, backticks, and semicolons are stripped without damaging string literals."""
    raw_1 = "```sql\nSELECT * FROM customers;\n```"
    assert clean_sql_query(raw_1) == "SELECT * FROM customers"

    raw_2 = "SELECT id, name FROM products WHERE stock < 10;"
    assert clean_sql_query(raw_2) == "SELECT id, name FROM products WHERE stock < 10"

    raw_3 = "```SELECT 1;```"
    assert clean_sql_query(raw_3) == "SELECT 1"

    # String literal ending with quote must NOT have quote stripped
    raw_4 = "SELECT id, name FROM customers WHERE city = 'New York';"
    assert clean_sql_query(raw_4) == "SELECT id, name FROM customers WHERE city = 'New York'"

    # Outer wrapped quotes around query
    raw_5 = "\"SELECT * FROM customers WHERE city = 'New York';\""
    assert clean_sql_query(raw_5) == "SELECT * FROM customers WHERE city = 'New York'"


# ------------------------------------------------------------------------------
# 2. Question Understanding Node Tests
# ------------------------------------------------------------------------------

def test_question_analysis_heuristics():
    """Verify intent detection and entity matching."""
    tables = ["customers", "products", "orders", "payments"]

    # Top ranking
    res1 = _fallback_analyze("Show the top 10 customers by total purchase", tables)
    assert res1.user_intent == "top_ranking"
    assert "customers" in res1.candidate_tables

    # Aggregation
    res2 = _fallback_analyze("What is the total revenue?", tables)
    assert res2.user_intent == "aggregation"

    # Temporal trend
    res3 = _fallback_analyze("Show monthly sales for this year", tables)
    assert res3.user_intent == "temporal_trend"

    # Ambiguity check
    res4 = _fallback_analyze("hi", tables)
    assert res4.is_ambiguous is True


# ------------------------------------------------------------------------------
# 3. Gemini API SQL Generation Tests
# ------------------------------------------------------------------------------

def is_gemini_key_available() -> bool:
    key = settings.GEMINI_API_KEY
    return bool(key and key.strip() not in ("", "your_gemini_api_key_here"))


def test_generate_sql_missing_api_key():
    """Verify clear error is raised if API key is missing."""
    with pytest.raises(ValueError) as excinfo:
        generate_sql(
            question="Show top 5 products",
            schema_context=MOCK_SCHEMA,
            api_key="",  # explicitly empty
        )
    assert "GEMINI_API_KEY is not configured" in str(excinfo.value)


@pytest.mark.skipif(not is_gemini_key_available(), reason="GEMINI_API_KEY not configured in .env")
def test_live_gemini_sql_generation_top_customers():
    """Verify live Gemini generates correct SELECT query for top customers."""
    try:
        result: SQLGenerationResult = generate_sql(
            question="Show the top 10 customers by total purchase amount",
            schema_context=MOCK_SCHEMA,
            dialect="mysql",
        )
    except Exception as e:
        if "getaddrinfo" in str(e) or "ConnectError" in str(e):
            pytest.skip(f"Network unavailable for live Gemini API call: {e}")
        raise

    assert result.sql_query is not None
    sql_upper = result.sql_query.upper()

    # Query must be read-only SELECT
    assert sql_upper.startswith("SELECT")
    assert "CUSTOMERS" in sql_upper
    assert "LIMIT" in sql_upper
    assert result.needs_clarification is False
    assert len(result.explanation) > 10


@pytest.mark.skipif(not is_gemini_key_available(), reason="GEMINI_API_KEY not configured in .env")
def test_live_gemini_sql_generation_low_stock():
    """Verify live Gemini generates query for products with stock below 10."""
    try:
        result: SQLGenerationResult = generate_sql(
            question="Which products have stock below 10?",
            schema_context=MOCK_SCHEMA,
            dialect="mysql",
        )
    except Exception as e:
        if "getaddrinfo" in str(e) or "ConnectError" in str(e):
            pytest.skip(f"Network unavailable for live Gemini API call: {e}")
        raise

    sql_upper = result.sql_query.upper()
    assert sql_upper.startswith("SELECT")
    assert "PRODUCTS" in sql_upper
    assert "STOCK" in sql_upper
    assert "< 10" in sql_upper or "<= 9" in sql_upper


@pytest.mark.skipif(not is_gemini_key_available(), reason="GEMINI_API_KEY not configured in .env")
def test_live_gemini_sql_error_correction():
    """Verify Gemini corrects a query when provided error feedback."""
    failed_sql = "SELECT customer_name, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5"
    error_msg = "Unknown column 'customer_name' in 'field list'"

    try:
        result: SQLGenerationResult = generate_sql(
            question="Show top 5 customers",
            schema_context=MOCK_SCHEMA,
            dialect="mysql",
            previous_sql=failed_sql,
            error_feedback=error_msg,
        )
    except Exception as e:
        if "getaddrinfo" in str(e) or "ConnectError" in str(e):
            pytest.skip(f"Network unavailable for live Gemini API call: {e}")
        raise

    sql_upper = result.sql_query.upper()
    assert sql_upper.startswith("SELECT")
    # Must use `name` instead of `customer_name`
    assert "NAME" in sql_upper
    assert "CUSTOMER_NAME" not in sql_upper
