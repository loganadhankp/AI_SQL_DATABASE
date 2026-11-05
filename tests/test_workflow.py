"""
Tests for Phase 7 & 8: LangGraph Workflow & Self-Healing Routing.
Verifies the complete agent loop, state transitions, conditional edges,
and business observations.
"""

import pytest
from sqlalchemy import create_engine, text
from backend.graph.workflow import analyst_graph
from backend.graph.state import AgentState


@pytest.fixture
def mock_db_engine():
    """Provides an SQLite database with products for deterministic workflow testing."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            );
        """)
        )
        conn.execute(
            text("""
            INSERT INTO products VALUES 
            (1, 'Laptop', 'Computers', 1200.0, 15),
            (2, 'Mouse', 'Accessories', 25.0, 80),
            (3, 'Monitor', 'Displays', 300.0, 5),
            (4, 'Keyboard', 'Accessories', 75.0, 40);
        """)
        )
        conn.commit()
    return engine


def test_workflow_graph_compilation():
    """Verify LangGraph compiles with valid entrypoint and nodes."""
    assert analyst_graph is not None


def test_workflow_ambiguous_question(mock_db_engine):
    """Verify ambiguous requests route to clarification without query execution."""
    initial_state: AgentState = {
        "user_question": "hi",  # Too short/ambiguous
        "connection_id": 1,
        "database_name": "test_db",
        "dialect": "sqlite",
        "engine": mock_db_engine,
        "chat_history": [],
        "available_tables": ["products"],
        "candidate_tables": [],
        "schema_context": "",
        "generated_sql": None,
        "sanitized_sql": None,
        "sql_explanation": None,
        "is_valid": False,
        "validation_error": None,
        "execution_result": None,
        "error_message": None,
        "error_category": None,
        "retry_count": 0,
        "max_retries": 2,
        "final_explanation": None,
        "observations": [],
        "suggested_chart": None,
        "needs_clarification": False,
        "clarification_message": None,
        "workflow_status": "in_progress",
        "execution_steps": [],
    }

    final_state = analyst_graph.invoke(initial_state)

    assert final_state["workflow_status"] == "clarification_needed"
    assert final_state["needs_clarification"] is True
    assert final_state["clarification_message"] is not None
    # Database execution should never have happened
    assert final_state["execution_result"] is None


def test_workflow_successful_execution(mock_db_engine, monkeypatch):
    """Verify full 8-node workflow execution and chart suggestion."""

    # Mock SQL generation to return valid SQL without needing external LLM API
    from backend.schemas.query_generation import SQLGenerationResult

    def mock_generate_sql(**kwargs):
        return SQLGenerationResult(
            sql_query="SELECT name, category, price, stock FROM products WHERE stock < 10",
            explanation="Selects products with low stock count below 10.",
            relevant_tables=["products"],
            confidence_score=0.95,
        )

    monkeypatch.setattr("backend.graph.nodes.generate_sql", mock_generate_sql)

    initial_state: AgentState = {
        "user_question": "Which products have stock below 10?",
        "connection_id": 1,
        "database_name": "test_db",
        "dialect": "sqlite",
        "engine": mock_db_engine,
        "chat_history": [],
        "available_tables": ["products"],
        "candidate_tables": [],
        "schema_context": "",
        "generated_sql": None,
        "sanitized_sql": None,
        "sql_explanation": None,
        "is_valid": False,
        "validation_error": None,
        "execution_result": None,
        "error_message": None,
        "error_category": None,
        "retry_count": 0,
        "max_retries": 2,
        "final_explanation": None,
        "observations": [],
        "suggested_chart": None,
        "needs_clarification": False,
        "clarification_message": None,
        "workflow_status": "in_progress",
        "execution_steps": [],
    }

    final_state = analyst_graph.invoke(initial_state)

    assert final_state["workflow_status"] == "completed"
    assert final_state["is_valid"] is True
    assert final_state["execution_result"] is not None
    assert final_state["execution_result"]["row_count"] == 1
    assert final_state["execution_result"]["rows"][0]["name"] == "Monitor"

    # Verify business analysis & chart
    assert final_state["final_explanation"] is not None
    assert len(final_state["observations"]) > 0

    # Verify execution timeline contains steps for frontend progress bar
    node_names = [s["node"] for s in final_state["execution_steps"]]
    assert "question_understanding" in node_names
    assert "schema_inspection" in node_names
    assert "sql_generation" in node_names
    assert "sql_validation" in node_names
    assert "database_execution" in node_names
    assert "result_analysis" in node_names
    assert "response_generation" in node_names
