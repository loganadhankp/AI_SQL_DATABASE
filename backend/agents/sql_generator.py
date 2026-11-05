"""
SQL Generation Agent Node.
Uses Google Gemini API to translate natural language questions into safe, optimized,
dialect-compliant SQL queries using dynamic live database schema context.
Supports error-feedback injection for self-healing query correction.
"""

import re
import time
import logging
from typing import Optional, List
from google import genai
from google.genai import types
from backend.config import get_settings
from backend.schemas.query_generation import SQLGenerationResult

logger = logging.getLogger(__name__)

settings = get_settings()


def clean_sql_query(raw_sql: str) -> str:
    """
    Cleans and strips markdown fences, backticks, or trailing semicolons
    to ensure pure executable SQL without stripping internal string literals.
    """
    if not raw_sql:
        return ""

    cleaned = raw_sql.strip()

    # Remove markdown code blocks like ```sql ... ```
    cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # Strip surrounding quotes ONLY if the entire query was wrapped in outer quotes
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        inner = cleaned[1:-1].strip()
        if re.match(r"^(SELECT|WITH)\b", inner, flags=re.IGNORECASE):
            cleaned = inner

    # Strip trailing semicolon so LIMIT or wraps can be applied cleanly
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    return cleaned


def generate_sql(
    question: str,
    schema_context: str,
    dialect: str = "mysql",
    error_feedback: Optional[str] = None,
    previous_sql: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> SQLGenerationResult:
    """
    Generates structured SQL query using Google Gemini API.
    Injects dynamic schema and previous error feedback if retrying.
    """
    active_key = api_key if api_key is not None else settings.GEMINI_API_KEY
    active_model = model or settings.GEMINI_MODEL

    if not active_key or active_key.strip() in ("", "your_gemini_api_key_here"):
        raise ValueError(
            "GEMINI_API_KEY is not configured. Please add your Google Gemini API key to the .env file. "
            "Get one for free at https://aistudio.google.com/"
        )

    client = genai.Client(api_key=active_key)

    # Error recovery context block
    error_section = ""
    if error_feedback and previous_sql:
        error_section = f"""
CRITICAL - PREVIOUS ATTEMPT FAILED:
The previous SQL query failed during execution:
Failed Query: `{previous_sql}`
Database Error: {error_feedback}

INSTRUCTION: Analyze this error message carefully. Identify why it failed (e.g., wrong column name, syntax error, missing GROUP BY, or invalid join), and generate a corrected SQL query that completely avoids this error.
"""

    prompt = f"""You are an elite Principal Database Engineer and SQL Architect.
Your task is to write a single, highly-optimized, read-only SQL query to answer the user's question.

SQL DIALECT: {dialect.upper()} (MySQL 8.0)

LIVE DATABASE SCHEMA:
{schema_context}
{error_section}
USER QUESTION:
"{question}"

MANDATORY RULES:
1. ONLY produce a single read-only `SELECT` statement.
2. NEVER produce DROP, ALTER, DELETE, UPDATE, INSERT, TRUNCATE, CREATE, GRANT, REVOKE, or stored procedures.
3. Use the explicit foreign key relationships provided in the schema to perform necessary `JOIN`s correctly.
4. When calculating aggregations, use meaningful column aliases (e.g., `SUM(...) AS total_revenue`, `COUNT(...) AS order_count`).
5. For "top N" or ranking questions, always include appropriate `ORDER BY ... DESC LIMIT N`.
6. For date-based questions in MySQL, use standard MySQL date functions:
   - Current date/time: `NOW()` or `CURDATE()`
   - Relative intervals: `DATE_SUB(NOW(), INTERVAL 1 MONTH)`, `INTERVAL 7 DAY`
   - Year/Month extraction: `YEAR(order_date)`, `MONTH(order_date)`, `DATE_FORMAT(order_date, '%Y-%m')`
7. For questions like "customers who have never placed an order", use `LEFT JOIN ... WHERE ... IS NULL` or `NOT EXISTS`.
8. Do NOT assume or invent any columns or tables not listed in the provided schema.
9. If the user question is completely impossible to answer with the available tables, set `needs_clarification = True` and write a polite `clarification_question`.

Return structured JSON conforming to the requested schema.
"""

    # Assemble candidate models with automatic high-availability fallbacks
    models_to_try = []
    if model:
        models_to_try.append(model)
    elif active_model:
        models_to_try.append(active_model)

    for fallback in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    last_error = None
    for attempt_model in models_to_try:
        try:
            response = client.models.generate_content(
                model=attempt_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SQLGenerationResult,
                    temperature=0.0,
                ),
            )

            result = SQLGenerationResult.model_validate_json(response.text)
            result.sql_query = clean_sql_query(result.sql_query)
            return result

        except Exception as e:
            err_str = str(e)
            last_error = e
            logger.warning(
                f"Model '{attempt_model}' failed: {err_str[:120]}. Checking fallback..."
            )
            # If 503 (high demand), 429 (rate limit), 404 (model unavailable), try next candidate
            if any(code in err_str for code in ["503", "429", "404", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "NOT_FOUND"]):
                time.sleep(0.5)
                continue
            # For non-recoverable client/syntax errors, raise directly
            raise RuntimeError(f"Gemini SQL Generation failed: {err_str}") from e

    raise RuntimeError(
        f"Gemini SQL Generation failed across models ({', '.join(models_to_try)}): {str(last_error)}"
    ) from last_error
