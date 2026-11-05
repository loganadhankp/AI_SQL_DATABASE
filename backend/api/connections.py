"""
Database Connection Management & Schema Explorer Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.connection import get_db, DatabaseConnectionManager
from backend.database.models import User, DatabaseConnection
from backend.schemas.api_schemas import (
    ConnectionCreate,
    ConnectionTestRequest,
    ConnectionOut,
)
from backend.schemas.schema_info import DatabaseSchemaMetadata, TablePreview
from backend.services.auth_service import get_current_user
from backend.services.encryption import encrypt_password
from backend.tools.schema_inspector import SchemaInspector

router = APIRouter(prefix="/api/connections", tags=["Database Connections"])


@router.post("/test")
def test_connection_endpoint(payload: ConnectionTestRequest):
    """Tests connectivity to a MySQL database with provided credentials."""
    result = DatabaseConnectionManager.test_connection(
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        username=payload.username,
        password=payload.password,
        dialect=payload.dialect,
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )
    return result


@router.post("", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
def create_connection(
    payload: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Saves a new external database connection configuration with encrypted credentials."""
    # Test connection first to verify validity
    test_res = DatabaseConnectionManager.test_connection(
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        username=payload.username,
        password=payload.password,
        dialect=payload.dialect,
    )
    if not test_res["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot save connection. Test failed: {test_res['message']}",
        )

    encrypted = encrypt_password(payload.password)
    new_conn = DatabaseConnection(
        user_id=current_user.id,
        connection_name=payload.connection_name.strip(),
        dialect=payload.dialect.lower().strip(),
        host=payload.host.strip(),
        port=payload.port,
        database_name=payload.database_name.strip(),
        username=payload.username.strip(),
        encrypted_password=encrypted,
    )
    db.add(new_conn)
    db.commit()
    db.refresh(new_conn)
    return ConnectionOut.model_validate(new_conn)


@router.get("", response_model=List[ConnectionOut])
def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists saved database connections for the current user."""
    connections = db.query(DatabaseConnection).filter(
        DatabaseConnection.user_id == current_user.id
    ).all()
    return [ConnectionOut.model_validate(c) for c in connections]


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    conn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes a saved database connection."""
    conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == conn_id,
        DatabaseConnection.user_id == current_user.id,
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")

    DatabaseConnectionManager.remove_engine(conn.id)
    db.delete(conn)
    db.commit()
    return None


@router.get("/{conn_id}/schema", response_model=DatabaseSchemaMetadata)
def get_connection_schema(
    conn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Introspects and returns full database schema tree."""
    conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == conn_id,
        DatabaseConnection.user_id == current_user.id,
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")

    engine = DatabaseConnectionManager.get_engine_for_connection(
        connection_id=conn.id,
        host=conn.host,
        port=conn.port,
        database_name=conn.database_name,
        username=conn.username,
        encrypted_password=conn.encrypted_password,
        dialect=conn.dialect,
    )

    return SchemaInspector.inspect_database(engine, conn.database_name)


@router.get("/{conn_id}/tables", response_model=List[str])
def get_connection_tables(
    conn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns list of accessible table names."""
    conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == conn_id,
        DatabaseConnection.user_id == current_user.id,
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")

    engine = DatabaseConnectionManager.get_engine_for_connection(
        connection_id=conn.id,
        host=conn.host,
        port=conn.port,
        database_name=conn.database_name,
        username=conn.username,
        encrypted_password=conn.encrypted_password,
        dialect=conn.dialect,
    )
    return SchemaInspector.get_table_names(engine)


@router.get("/{conn_id}/tables/{table_name}", response_model=TablePreview)
def get_table_preview_endpoint(
    conn_id: int,
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns safe 5-row sample preview of a specified table."""
    conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == conn_id,
        DatabaseConnection.user_id == current_user.id,
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")

    engine = DatabaseConnectionManager.get_engine_for_connection(
        connection_id=conn.id,
        host=conn.host,
        port=conn.port,
        database_name=conn.database_name,
        username=conn.username,
        encrypted_password=conn.encrypted_password,
        dialect=conn.dialect,
    )
    return SchemaInspector.get_table_preview(engine, table_name, limit=5)
