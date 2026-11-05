"""
LangGraph Shared State Schema for AI SQL Database Analyst.
Tracks execution context, generated SQL, validation status, retry loops,
and final insights across all workflow nodes.
"""

from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
import operator


def add_steps(existing: List[Dict[str, Any]], new_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Accumulates execution timeline steps."""
    return existing + new_steps


class AgentState(TypedDict):
    """Shared state object flowing through all LangGraph nodes."""

    # 1. Inputs
    user_question: str
    connection_id: int
    database_name: str
    dialect: str
    engine: Any  # SQLAlchemy Engine instance

    # 2. Context & History
    chat_history: List[Dict[str, str]]
    available_tables: List[str]
    candidate_tables: List[str]
    schema_context: str

    # 3. SQL Generation & Validation
    generated_sql: Optional[str]
    sanitized_sql: Optional[str]
    sql_explanation: Optional[str]
    is_valid: bool
    validation_error: Optional[str]

    # 4. Database Execution & Errors
    execution_result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_category: Optional[str]
    retry_count: int
    max_retries: int

    # 5. Output Insights & Charts
    final_explanation: Optional[str]
    observations: List[str]
    suggested_chart: Optional[Dict[str, Any]]
    needs_clarification: bool
    clarification_message: Optional[str]
    workflow_status: str  # 'in_progress', 'completed', 'failed', 'clarification_needed'

    # 6. Audit & Progress Timeline
    execution_steps: Annotated[List[Dict[str, Any]], add_steps]
