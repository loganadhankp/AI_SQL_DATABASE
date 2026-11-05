"""
Safe Database Execution Engine.
Executes validated read-only SQL queries on target MySQL databases with:
- Execution duration measurement (milliseconds).
- Safe result serialization (Decimals, datetimes, dates, bytes).
- Query execution timeouts.
- Categorized error diagnostics (syntax, schema, permission, timeout).
"""

import time
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import text, Engine
from sqlalchemy.exc import (
    ProgrammingError,
    OperationalError,
    IntegrityError,
    DBAPIError,
)


class ExecutionResult(BaseModel):
    """Structured result returned by the database execution engine."""
    success: bool
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    error_category: Optional[str] = None  # 'syntax', 'schema', 'permission', 'timeout', 'unknown'


class DatabaseExecutor:
    """Safely executes validated queries with timeout and error classification."""

    DEFAULT_TIMEOUT_SECONDS = 10

    @classmethod
    def execute_query(
        cls,
        engine: Engine,
        sql_query: str,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> ExecutionResult:
        """
        Executes a validated read-only SQL statement and returns structured results.
        """
        start_time = time.perf_counter()

        try:
            with engine.connect() as conn:
                # Set execution timeout on MySQL connection if supported
                try:
                    if engine.dialect.name == "mysql":
                        # Set max_execution_time in milliseconds
                        conn.execute(text(f"SET max_execution_time = {timeout_seconds * 1000};"))
                except Exception:
                    pass

                # Execute the query
                result = conn.execute(text(sql_query))
                columns = list(result.keys()) if result.returns_rows else []
                raw_rows = result.fetchall() if result.returns_rows else []

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Serialize data types cleanly
            serialized_rows: List[Dict[str, Any]] = []
            for row in raw_rows:
                row_dict = {}
                for col_name, val in zip(columns, row):
                    if isinstance(val, (datetime, date)):
                        row_dict[col_name] = val.isoformat()
                    elif isinstance(val, Decimal):
                        row_dict[col_name] = float(val)
                    elif isinstance(val, bytes):
                        row_dict[col_name] = val.decode("utf-8", errors="replace")
                    else:
                        row_dict[col_name] = val
                serialized_rows.append(row_dict)

            return ExecutionResult(
                success=True,
                columns=columns,
                rows=serialized_rows,
                row_count=len(serialized_rows),
                execution_time_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            category = cls._categorize_error(e)
            error_str = cls._clean_error_message(e)

            return ExecutionResult(
                success=False,
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=elapsed_ms,
                error_message=error_str,
                error_category=category,
            )

    @staticmethod
    def _categorize_error(exc: Exception) -> str:
        """Classifies database errors for self-healing error recovery."""
        msg = str(exc).lower()

        if "timeout" in msg or "max_execution_time" in msg or "query execution was interrupted" in msg:
            return "timeout"
        if "access denied" in msg or "command denied" in msg or "permission" in msg:
            return "permission"
        if "unknown column" in msg or "no such column" in msg or "doesn't exist" in msg or "unknown table" in msg or "no such table" in msg:
            return "schema"
        if "syntax error" in msg or "check the manual" in msg or "1064" in msg:
            return "syntax"
        if isinstance(exc, ProgrammingError):
            return "schema"
        if isinstance(exc, OperationalError):
            return "connection"

        return "unknown"

    @staticmethod
    def _clean_error_message(exc: Exception) -> str:
        """Extracts concise error description without internal stack traces."""
        # Check for DBAPI orig error
        orig = getattr(exc, "orig", None)
        if orig and len(orig.args) > 1:
            # (1054, "Unknown column 'xyz' in 'field list'")
            return f"MySQL Error {orig.args[0]}: {orig.args[1]}"
        elif orig and len(orig.args) == 1:
            return f"MySQL Error: {orig.args[0]}"
        return str(exc).split("\n")[0]
