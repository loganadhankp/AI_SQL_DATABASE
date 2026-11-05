"""
Pydantic Schemas for FastAPI API Request and Response Payloads.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


# ------------------------------------------------------------------------------
# Auth Schemas
# ------------------------------------------------------------------------------

class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ------------------------------------------------------------------------------
# Database Connection Schemas
# ------------------------------------------------------------------------------

class ConnectionCreate(BaseModel):
    connection_name: str
    dialect: str = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    database_name: str
    username: str
    password: str


class ConnectionTestRequest(BaseModel):
    dialect: str = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    database_name: str
    username: str
    password: str


class ConnectionOut(BaseModel):
    id: int
    connection_name: str
    dialect: str
    host: str
    port: int
    database_name: str
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# AI Analyst Query Schemas
# ------------------------------------------------------------------------------

class QueryRequest(BaseModel):
    connection_id: int
    question: str
    session_id: Optional[str] = None


class ExecutionStepOut(BaseModel):
    node: str
    status: str
    duration_ms: float
    detail: str


class QueryResponse(BaseModel):
    query_id: Optional[int] = None
    question: str
    workflow_status: str  # 'completed', 'failed', 'clarification_needed'
    generated_sql: Optional[str] = None
    final_explanation: Optional[str] = None
    observations: List[str] = []
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    execution_time_ms: float = 0.0
    suggested_chart: Optional[Dict[str, Any]] = None
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    error_message: Optional[str] = None
    execution_steps: List[ExecutionStepOut] = []


# ------------------------------------------------------------------------------
# Query History Schemas
# ------------------------------------------------------------------------------

class HistoryOut(BaseModel):
    id: int
    connection_id: Optional[int]
    question: str
    generated_sql: Optional[str]
    execution_status: str
    execution_time_ms: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Dashboard Overview Schemas
# ------------------------------------------------------------------------------

class DashboardOverviewOut(BaseModel):
    total_connections: int
    active_connection: Optional[ConnectionOut] = None
    accessible_tables_count: int = 0
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    recent_history: List[HistoryOut] = []
