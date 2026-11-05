"""
API smoke tests for FastAPI server entrypoint.
Direct endpoint testing ensures instant verification.
"""

from backend.main import root, health_check


def test_root_endpoint():
    """Verify that root endpoint returns project metadata."""
    data = root()
    assert data["project"] == "AI SQL Database Analyst"
    assert data["status"] == "online"


def test_health_check_endpoint():
    """Verify that /health endpoint is operational."""
    data = health_check()
    assert data["status"] == "healthy"
