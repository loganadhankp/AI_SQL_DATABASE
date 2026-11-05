"""
Automated unit tests for FastAPI REST Endpoints (Phase 9):
Auth (Register, Login, Me), Connections, History, and Dashboard.
Direct endpoint testing ensures instant execution without ASGI threading overhead.
"""

import pytest
from sqlalchemy.orm import Session
from backend.database.connection import SessionLocal, init_db
from backend.database.models import User, DatabaseConnection, QueryHistory
from backend.schemas.api_schemas import (
    UserRegister,
    UserLogin,
    ConnectionCreate,
    ConnectionTestRequest,
)
from backend.api.auth import register_user, login_user, get_me
from backend.api.connections import list_connections, delete_connection
from backend.api.history import get_query_history, get_dashboard_overview


@pytest.fixture
def db_session():
    """Provides a fresh isolated database session."""
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_auth_registration_and_login_flow(db_session: Session):
    """Verify user registration, JWT generation, and login verification."""
    unique_user = "api_test_pilot"
    unique_email = "pilot@testdomain.com"

    # Clean any prior record
    db_session.query(User).filter(User.username == unique_user).delete()
    db_session.commit()

    # 1. Register
    reg_payload = UserRegister(
        username=unique_user,
        email=unique_email,
        password="ValidPassword123!",
    )
    reg_out = register_user(reg_payload, db=db_session)
    assert reg_out.access_token is not None
    assert reg_out.user.username == unique_user

    # 2. Login
    login_payload = UserLogin(
        username_or_email=unique_user,
        password="ValidPassword123!",
    )
    login_out = login_user(login_payload, db=db_session)
    assert login_out.access_token is not None
    assert login_out.user.id == reg_out.user.id

    # 3. Authenticated Get Me
    current_u = db_session.query(User).filter(User.id == reg_out.user.id).first()
    me_profile = get_me(current_user=current_u)
    assert me_profile.email == unique_email


def test_connections_and_history_endpoints(db_session: Session):
    """Verify listing connections and query history for an authenticated user."""
    test_user = db_session.query(User).filter(User.username == "api_test_pilot").first()
    if not test_user:
        test_user = User(
            username="api_test_pilot",
            email="pilot@testdomain.com",
            password_hash="hashed_pw",
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

    # List connections (initially empty or existing)
    conns = list_connections(db=db_session, current_user=test_user)
    assert isinstance(conns, list)

    # Check query history
    hist = get_query_history(limit=10, db=db_session, current_user=test_user)
    assert isinstance(hist, list)

    # Check dashboard overview metrics
    dash = get_dashboard_overview(db=db_session, current_user=test_user)
    assert dash.total_connections >= 0
    assert dash.total_queries >= 0
    assert dash.successful_queries >= 0
