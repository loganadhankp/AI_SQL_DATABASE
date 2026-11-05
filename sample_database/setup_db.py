"""
Database setup and verification script.
Connects to MySQL, executes sample_database/ecommerce.sql, and verifies row counts.
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

DB_HOST = os.getenv("SAMPLE_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("SAMPLE_DB_PORT", 3306))
DB_USER = os.getenv("SAMPLE_DB_USER", "root")
DB_PASSWORD = os.getenv("SAMPLE_DB_PASSWORD", "")
DB_NAME = os.getenv("SAMPLE_DB_NAME", "ecommerce_db")

SQL_FILE_PATH = os.path.join(os.path.dirname(__file__), "ecommerce.sql")


def execute_sql_file():
    print("=" * 60)
    print("  AI SQL Database Analyst - E-Commerce DB Setup")
    print("=" * 60)
    print(f"Connecting to MySQL at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")

    try:
        # Connect to MySQL server without selecting a database first
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        print("Connected to MySQL server successfully!")
    except pymysql.MySQLError as e:
        print(f"\n[ERROR] Failed to connect to MySQL: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure MySQL is running locally or via Docker (`docker compose up -d mysql`).")
        print("2. Check SAMPLE_DB_USER and SAMPLE_DB_PASSWORD in your .env file.")
        print("3. Verify SAMPLE_DB_HOST and SAMPLE_DB_PORT (default 127.0.0.1:3306).")
        sys.exit(1)

    try:
        with connection.cursor() as cursor:
            print(f"Reading SQL file from: {SQL_FILE_PATH}")
            with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Strip comment lines FIRST before splitting by semicolon
            clean_lines = []
            for line in sql_content.splitlines():
                stripped = line.strip()
                if stripped.startswith("--") or stripped.startswith("/*"):
                    continue
                clean_lines.append(line)
            clean_sql = "\n".join(clean_lines)

            # Execute individual statements separated by semicolon
            statements = [stmt.strip() for stmt in clean_sql.split(";") if stmt.strip()]

            print(f"Executing {len(statements)} SQL statements...")
            for i, clean_stmt in enumerate(statements, 1):
                try:
                    cursor.execute(clean_stmt)
                except pymysql.MySQLError as err:
                    # Ignore harmless drop table warnings if fresh
                    if "Unknown table" in str(err):
                        continue
                    print(f"\n[FATAL ERROR] Statement #{i} failed:\n{err}\nStatement preview: {clean_stmt[:120]}...")
                    raise err

            print("[SUCCESS] All schema and seed statements executed successfully!")

            # Verify table row counts
            print("\n" + "-" * 40)
            print("  Table Verification & Row Counts:")
            print("-" * 40)
            tables = ["customers", "products", "orders", "order_items", "payments"]
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) AS total FROM ecommerce_db.{table}")
                count = cursor.fetchone()["total"]
                print(f"  • {table:<15} : {count:>5} records")

            # Check read-only user access
            print("-" * 40)
            print("Testing Read-Only user ('analyst_readonly')...")
            cursor.execute("SELECT user, host FROM mysql.user WHERE user = 'analyst_readonly'")
            ro_user = cursor.fetchone()
            if ro_user:
                print("  • User 'analyst_readonly'@'%' confirmed in mysql.user")
            print("=" * 60)
            print("  Phase 2 Database Setup Completed Successfully!")
            print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Failed during database population: {e}")
        sys.exit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    execute_sql_file()
