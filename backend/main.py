"""
AI SQL Database Analyst - Backend Entry Point
FastAPI application setup with CORS, lifespan database initialization,
and modular REST routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.database.connection import init_db
from backend.api import auth, connections, analyst, history

settings = get_settings()

# Initialize application metadata tables
init_db()

app = FastAPI(
    title="AI SQL Database Analyst API",
    description="Agentic AI-Powered Natural Language to SQL Analytics Platform",
    version="1.0.0",
    debug=settings.DEBUG,
)

# Enable CORS for local frontend client (Vite on http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(connections.router)
app.include_router(analyst.router)
app.include_router(history.router)


@app.get("/")
def root():
    """Root welcome message."""
    return {
        "project": "AI SQL Database Analyst",
        "status": "online",
        "documentation": "/docs",
    }


@app.get("/health")
def health_check():
    """Application health status check."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }
