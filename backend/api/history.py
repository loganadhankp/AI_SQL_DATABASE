"""
Query Audit History & Dashboard Overview Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database.connection import get_db, DatabaseConnectionManager
from backend.database.models import User, DatabaseConnection, QueryHistory
from backend.schemas.api_schemas import HistoryOut, DashboardOverviewOut, ConnectionOut
from backend.services.auth_service import get_current_user
from backend.tools.schema_inspector import SchemaInspector

router = APIRouter(tags=["Query History & Dashboard"])


@router.get("/api/history", response_model=List[HistoryOut])
def get_query_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves list of past executed natural language questions."""
    history = (
        db.query(QueryHistory)
        .filter(QueryHistory.user_id == current_user.id)
        .order_by(desc(QueryHistory.created_at))
        .limit(min(limit, 100))
        .all()
    )
    return [HistoryOut.model_validate(h) for h in history]


@router.delete("/api/history/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_query_history_item(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes an entry from query history."""
    item = (
        db.query(QueryHistory)
        .filter(QueryHistory.id == query_id, QueryHistory.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found.")

    db.delete(item)
    db.commit()
    return None


@router.get("/api/dashboard/overview", response_model=DashboardOverviewOut)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregates high-level dashboard metrics for KPI widgets."""
    connections = (
        db.query(DatabaseConnection)
        .filter(DatabaseConnection.user_id == current_user.id)
        .all()
    )
    total_conns = len(connections)

    # Active connection (defaulting to the first saved connection)
    active_conn = connections[0] if total_conns > 0 else None
    accessible_tables = 0

    if active_conn:
        try:
            engine = DatabaseConnectionManager.get_engine_for_connection(
                connection_id=active_conn.id,
                host=active_conn.host,
                port=active_conn.port,
                database_name=active_conn.database_name,
                username=active_conn.username,
                encrypted_password=active_conn.encrypted_password,
                dialect=active_conn.dialect,
            )
            tables = SchemaInspector.get_table_names(engine)
            accessible_tables = len(tables)
        except Exception:
            accessible_tables = 0

    queries = (
        db.query(QueryHistory)
        .filter(QueryHistory.user_id == current_user.id)
        .order_by(desc(QueryHistory.created_at))
        .all()
    )
    total_q = len(queries)
    successful_q = sum(1 for q in queries if q.execution_status == "completed" or q.execution_status == "success")
    failed_q = sum(1 for q in queries if q.execution_status == "failed" or q.execution_status == "rejected")

    recent = queries[:5]

    return DashboardOverviewOut(
        total_connections=total_conns,
        active_connection=ConnectionOut.model_validate(active_conn) if active_conn else None,
        accessible_tables_count=accessible_tables,
        total_queries=total_q,
        successful_queries=successful_q,
        failed_queries=failed_q,
        recent_history=[HistoryOut.model_validate(h) for h in recent],
    )
