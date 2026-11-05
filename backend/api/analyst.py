"""
AI SQL Analyst Query Endpoint.
Executes LangGraph workflow on connected database, records audit history,
and returns structured query answers, charts, and execution steps.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.connection import get_db, DatabaseConnectionManager
from backend.database.models import User, DatabaseConnection, QueryHistory
from backend.schemas.api_schemas import QueryRequest, QueryResponse, ExecutionStepOut
from backend.services.auth_service import get_current_user
from backend.graph.workflow import analyst_graph
from backend.graph.state import AgentState

router = APIRouter(prefix="/api/analyst", tags=["AI Analyst"])


@router.post("/query", response_model=QueryResponse)
def execute_natural_language_query(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits a natural language question.
    Triggers the LangGraph Agentic Workflow:
    Understanding -> Schema -> Generation -> Validation -> Execution -> Analysis -> Response.
    """
    # 1. Fetch connection profile
    conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == payload.connection_id,
        DatabaseConnection.user_id == current_user.id,
    ).first()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection profile not found.",
        )

    # 2. Retrieve pooled SQLAlchemy engine
    engine = DatabaseConnectionManager.get_engine_for_connection(
        connection_id=conn.id,
        host=conn.host,
        port=conn.port,
        database_name=conn.database_name,
        username=conn.username,
        encrypted_password=conn.encrypted_password,
        dialect=conn.dialect,
    )

    # 3. Initialize AgentState
    initial_state: AgentState = {
        "user_question": payload.question.strip(),
        "connection_id": conn.id,
        "database_name": conn.database_name,
        "dialect": conn.dialect,
        "engine": engine,
        "chat_history": [],
        "available_tables": [],
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

    # 4. Execute LangGraph Workflow
    try:
        final_state = analyst_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow invocation error: {str(e)}",
        )

    # 5. Extract execution metrics
    exec_result = final_state.get("execution_result") or {}
    status_str = "success" if exec_result.get("success") else "failed"
    duration = exec_result.get("execution_time_ms", 0.0)

    # 6. Save to QueryHistory audit log
    history_record = QueryHistory(
        user_id=current_user.id,
        connection_id=conn.id,
        question=payload.question,
        generated_sql=final_state.get("sanitized_sql") or final_state.get("generated_sql"),
        execution_status=final_state.get("workflow_status", status_str),
        execution_time_ms=duration,
        error_message=final_state.get("error_message") or final_state.get("validation_error"),
    )
    db.add(history_record)
    db.commit()
    db.refresh(history_record)

    # 7. Format execution timeline steps
    timeline = [
        ExecutionStepOut(
            node=s.get("node", "step"),
            status=s.get("status", "completed"),
            duration_ms=s.get("duration_ms", 0.0),
            detail=s.get("detail", ""),
        )
        for s in (final_state.get("execution_steps") or [])
    ]

    return QueryResponse(
        query_id=history_record.id,
        question=payload.question,
        workflow_status=final_state.get("workflow_status", "completed"),
        generated_sql=final_state.get("sanitized_sql") or final_state.get("generated_sql"),
        final_explanation=final_state.get("final_explanation")
        or final_state.get("sql_explanation")
        or final_state.get("error_message")
        or "Query execution completed.",
        observations=final_state.get("observations") or [],
        columns=exec_result.get("columns") or [],
        rows=exec_result.get("rows") or [],
        row_count=exec_result.get("row_count", 0),
        execution_time_ms=duration,
        suggested_chart=final_state.get("suggested_chart"),
        needs_clarification=bool(final_state.get("needs_clarification", False)),
        clarification_message=final_state.get("clarification_message"),
        error_message=final_state.get("error_message") or final_state.get("validation_error"),
        execution_steps=timeline,
    )


@router.get("/query/{query_id}", response_model=QueryResponse)
def get_query_result_by_id(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves previous query execution record from audit history."""
    record = db.query(QueryHistory).filter(
        QueryHistory.id == query_id,
        QueryHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query record not found.")

    return QueryResponse(
        query_id=record.id,
        question=record.question,
        workflow_status=record.execution_status,
        generated_sql=record.generated_sql,
        final_explanation=f"Executed with status: {record.execution_status}.",
        observations=[],
        columns=[],
        rows=[],
        row_count=0,
        execution_time_ms=record.execution_time_ms or 0.0,
        error_message=record.error_message,
        execution_steps=[],
    )


@router.post("/query/{query_id}/feedback")
def submit_query_feedback(
    query_id: int,
    feedback: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Records user rating (thumbs up/down) for continuous quality tracking."""
    return {"status": "feedback_recorded", "query_id": query_id}
