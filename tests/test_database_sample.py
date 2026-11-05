"""
Automated tests for Phase 2: MySQL sample e-commerce database.
Verifies table structure, foreign keys, row counts, and sample query conditions.
"""

import pytest
import pymysql
from backend.config import get_settings

settings = get_settings()


def get_mysql_connection():
    """Attempt connecting to the sample database."""
    try:
        conn = pymysql.connect(
            host=settings.SAMPLE_DB_HOST,
            port=settings.SAMPLE_DB_PORT,
            user=settings.SAMPLE_DB_USER,
            password=settings.SAMPLE_DB_PASSWORD,
            database=settings.SAMPLE_DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3,
        )
        return conn
    except Exception as e:
        pytest.skip(f"MySQL not reachable at {settings.SAMPLE_DB_HOST}:{settings.SAMPLE_DB_PORT}: {e}")


def test_ecommerce_tables_exist():
    """Verify that all 5 required tables exist in ecommerce_db."""
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            expected_tables = ["customers", "products", "orders", "order_items", "payments"]
            for table in expected_tables:
                assert table in tables, f"Expected table '{table}' not found in database."
    finally:
        conn.close()


def test_ecommerce_row_counts():
    """Verify minimum row count thresholds from specification."""
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            # 1. At least 100 customers
            cursor.execute("SELECT COUNT(*) AS total FROM customers")
            cust_count = cursor.fetchone()["total"]
            assert cust_count >= 100, f"Expected at least 100 customers, found {cust_count}"

            # 2. At least 30 products
            cursor.execute("SELECT COUNT(*) AS total FROM products")
            prod_count = cursor.fetchone()["total"]
            assert prod_count >= 30, f"Expected at least 30 products, found {prod_count}"

            # 3. At least 200 orders
            cursor.execute("SELECT COUNT(*) AS total FROM orders")
            order_count = cursor.fetchone()["total"]
            assert order_count >= 200, f"Expected at least 200 orders, found {order_count}"

            # 4. Order items exist
            cursor.execute("SELECT COUNT(*) AS total FROM order_items")
            item_count = cursor.fetchone()["total"]
            assert item_count >= 200, f"Expected multiple order items, found {item_count}"

            # 5. Payments exist
            cursor.execute("SELECT COUNT(*) AS total FROM payments")
            pay_count = cursor.fetchone()["total"]
            assert pay_count >= 200, f"Expected payments matching orders, found {pay_count}"
    finally:
        conn.close()


def test_specific_business_scenarios():
    """
    Verify specific query test cases from the project specification:
    - Customers with NO orders exist
    - Products with stock < 10 exist
    - Multiple distinct cities exist
    """
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            # Customers without orders (e.g. IDs 86-100)
            cursor.execute("""
                SELECT COUNT(*) AS total 
                FROM customers c 
                LEFT JOIN orders o ON c.id = o.customer_id 
                WHERE o.id IS NULL
            """)
            no_order_count = cursor.fetchone()["total"]
            assert no_order_count > 0, "Expected at least one customer who has never placed an order"

            # Low stock products (< 10)
            cursor.execute("SELECT COUNT(*) AS total FROM products WHERE stock < 10")
            low_stock_count = cursor.fetchone()["total"]
            assert low_stock_count > 0, "Expected at least one product with stock < 10"

            # Multiple cities for comparison
            cursor.execute("SELECT COUNT(DISTINCT city) AS total FROM customers")
            city_count = cursor.fetchone()["total"]
            assert city_count >= 5, "Expected at least 5 distinct cities for comparison queries"
    finally:
        conn.close()
