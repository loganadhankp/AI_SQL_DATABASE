"""
Initial environment and dependency verification test.
Ensures that all foundational libraries are properly installed and importable.
"""

def test_imports():
    """Verify core packages can be imported without errors."""
    import fastapi
    import sqlalchemy
    import pydantic
    import langgraph
    import sqlglot
    import jwt
    import dotenv

    assert fastapi.__version__ is not None
    assert sqlalchemy.__version__ is not None
    assert pydantic.__version__ is not None
    assert sqlglot.__version__ is not None
    print("\n[SUCCESS] Core libraries successfully imported!")
