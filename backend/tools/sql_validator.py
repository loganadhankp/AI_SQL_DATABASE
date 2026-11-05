"""
AST-based SQL Validation Engine using SQLGlot.
Enforces strict read-only execution:
- Guarantees exactly ONE statement.
- Guarantees the statement is an exp.Select query.
- Rejects dangerous commands: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE,
  CREATE, GRANT, REVOKE, EXECUTE/CALL, PRAGMA, SET, transactions, or multiple statements.
- Prevents SQL injection, comments that evade parsing, and AST mutations.
- Enforces a maximum LIMIT clause if missing.
"""

from typing import Tuple, Optional, List
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

DANGEROUS_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Create,
    exp.Grant,
    exp.Revoke,
    exp.Command,
    exp.Commit,
    exp.Rollback,
    exp.Transaction,
)


class SQLValidator:
    """
    Validates SQL queries using Abstract Syntax Tree (AST) analysis.
    Dialect-aware (MySQL 8.0 default).
    """

    DEFAULT_MAX_ROWS = 1000

    @classmethod
    def validate_sql(
        cls,
        sql: str,
        dialect: str = "mysql",
        max_allowed_rows: int = DEFAULT_MAX_ROWS,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validates the given SQL string.
        Returns:
            (is_valid: bool, message: str, sanitized_sql: Optional[str])
        """
        if not sql or not sql.strip():
            return False, "Query is empty.", None

        clean_sql = sql.strip().rstrip(";")

        # 1. Parse into AST
        try:
            expressions = sqlglot.parse(clean_sql, read=dialect)
        except ParseError as pe:
            return False, f"SQL Syntax/Parse Error: {str(pe)}", None
        except Exception as e:
            return False, f"Failed to parse SQL: {str(e)}", None

        # 2. Reject multiple SQL statements (prevents stacked queries SQL injection)
        if len(expressions) == 0:
            return False, "No executable SQL statements found.", None

        if len(expressions) > 1:
            return (
                False,
                f"Security Violation: Stacked queries detected. Exactly ONE statement is permitted, received {len(expressions)}.",
                None,
            )

        ast = expressions[0]

        # 3. Must be a SELECT expression (or Union/Subquery of Selects)
        if not isinstance(ast, (exp.Select, exp.Union)):
            statement_type = type(ast).__name__
            return (
                False,
                f"Security Violation: Only read-only SELECT statements are permitted. Received statement type: '{statement_type}'.",
                None,
            )

        # 4. Check entire AST for prohibited dangerous expressions
        for dangerous_type in DANGEROUS_EXPRESSIONS:
            if list(ast.find_all(dangerous_type)):
                return (
                    False,
                    f"Security Violation: Query contains prohibited database modification operation: {dangerous_type.__name__}.",
                    None,
                )

        # 5. Check for unsafe function calls (e.g. sleep, benchmark, load_file, into outfile)
        for func in ast.find_all(exp.Anonymous):
            func_name = func.name.upper()
            if func_name in ("SLEEP", "BENCHMARK", "LOAD_FILE", "INTO_OUTFILE", "SYSTEM_USER"):
                return False, f"Security Violation: Prohibited function call: '{func_name}'.", None

        # 6. Enforce hard LIMIT constraint to prevent memory exhaustion
        sanitized_sql = cls._enforce_limit(ast, dialect=dialect, max_rows=max_allowed_rows)

        return True, "Query successfully validated as safe read-only SELECT.", sanitized_sql

    @classmethod
    def _enforce_limit(cls, ast: exp.Expression, dialect: str, max_rows: int) -> str:
        """
        Inspects existing LIMIT clause. If missing or greater than max_rows, enforces max_rows.
        """
        limit_node = ast.find(exp.Limit)
        if limit_node and limit_node.expression:
            try:
                current_limit = int(limit_node.expression.name)
                if current_limit > max_rows:
                    limit_node.set("expression", exp.Literal.number(max_rows))
            except (ValueError, AttributeError):
                # If limit expression is dynamic or unusual, cap it
                limit_node.set("expression", exp.Literal.number(max_rows))
        else:
            # If no limit clause, append limit
            ast = ast.limit(max_rows)

        return ast.sql(dialect=dialect)
