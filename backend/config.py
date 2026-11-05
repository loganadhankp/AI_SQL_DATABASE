"""
Application configuration management using Pydantic Settings.
Reads environment variables from .env file with safe defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "super-secret-development-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Internal metadata database (users, connections, history)
    APP_DATABASE_URL: str = "sqlite:///./app_metadata.db"

    # LLM Settings (Google Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # Target Sample MySQL Database (For testing and exploration)
    SAMPLE_DB_HOST: str = "127.0.0.1"
    SAMPLE_DB_PORT: int = 3306
    SAMPLE_DB_NAME: str = "ecommerce_db"
    SAMPLE_DB_USER: str = "root"
    SAMPLE_DB_PASSWORD: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()
