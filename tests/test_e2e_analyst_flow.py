"""
End-to-End Integration Test for AI SQL Database Analyst.
Simulates a user connecting their database, asking an analytical question,
and receiving validated SQL, execution results, and visualizations.
"""

import pytest
from sqlalchemy.orm import Session
from backend.database.connection import SessionLocal, init_db
from backend.database.models import User, DatabaseConnection, QueryHistory
from backend.schemas.api_schemas import QueryRequest
from backend.api.analyst import execute_natural_language_query
from backend.services.encryption import encrypt_password
from backend.config import get_settings

settings = get_settings()


@pytest.fixture
def test_user_and_connection():
    """Sets up an authenticated test user and active MySQL sample connection profile."""
    init_db()
    session = SessionLocal()

    # User
    user = session.query(User).filter(User.username == "e2e_analyst_user").first()
    if not user:
        user = User(
            username="e2e_analyst_user",
            email="e2e@analyst.com",
            password_hash="mock_hash",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    # Saved connection to ecommerce_db
    conn = session.query(DatabaseConnection).filter(
        DatabaseConnection.user_id == user.id,
        DatabaseConnection.database_name == settings.SAMPLE_DB_NAME,
    ).first()
    if not conn:
        conn = DatabaseConnection(
            user_id=user.id,
            connection_name="E-Commerce Store DB",
            dialect="mysql",
            host=settings.SAMPLE_DB_HOST,
            port=settings.SAMPLE_DB_PORT,
            database_name=settings.SAMPLE_DB_NAME,
            username=settings.SAMPLE_DB_USER,
            encrypted_password=encrypt_password(settings.SAMPLE_DB_PASSWORD),
        )
        session.add(conn)
        session.commit()
        session.refresh(conn)

    try:
        yield user, conn, session
    finally:
        session.close()


def test_e2e_query_execution_flow(test_user_and_connection, monkeypatch):
    """
    Simulates end-to-end question answering flow with mocked LLM output,
    testing live database query execution, validation, result analysis, and auditing.
    """
    user, conn, session = test_user_and_connection

    # Mock Gemini generation to return a valid query without requiring external network
    from backend.schemas.query_generation import SQLGenerationResult

    def mock_gen(**kwargs):
        return SQLGenerationResult(
            sql_query="""
                SELECT c.name, COUNT(o.id) AS total_orders
                FROM customers c
                JOIN orders o ON c.id = o.customer_id
                GROUP BY c.id, c.name
                ORDER BY total_orders DESC
                LIMIT 5
            """,
            explanation="Calculates top 5 customers by total number of orders placed.",
            relevant_tables=["customers", "orders"],
            confidence_score=0.98,
        )

    monkeypatch.setattr("backend.graph.nodes.generate_sql", mock_gen)

    request_payload = QueryRequest(
        connection_id=conn.id,
        question="Who are our top 5 most frequent customers?",
    )

    try:
        response = execute_natural_language_query(
            payload=request_payload,
            db=session,
            current_user=user,
        )
    except Exception as e:
        if "Can't connect to MySQL" in str(e) or "10013" in str(e) or "getaddrinfo" in str(e):
            pytest.skip(f"MySQL unreachable in offline/sandboxed test environment: {e}")
        raise

    # Verify query response contract
    assert response.workflow_status == "completed"
    assert response.generated_sql is not None
    assert "SELECT" in response.generated_sql.upper()
    assert response.row_count > 0
    assert len(response.rows) > 0
    assert len(response.columns) == 2
    assert "total_orders" in response.columns

    # Verify chart suggestion
    assert response.suggested_chart is not None
    assert response.suggested_chart["chart_type"] in ("bar", "pie", "line")

    # Verify audit log was recorded in database
    audit = session.query(QueryHistory).filter(QueryHistory.id == response.query_id).first()
    assert audit is not None
    assert audit.user_id == user.id
    assert audit.execution_status == "completed"
    assert audit.execution_time_ms > 0
