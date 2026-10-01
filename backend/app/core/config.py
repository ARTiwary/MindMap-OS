"""
Centralized application configuration.

All configuration is sourced from environment variables (see .env.example).
Nothing here should ever contain a real secret - defaults are for local dev only.
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Any of these being live in production means the deployer never set a real
# value - fail loudly at startup rather than quietly running insecurely.
_PLACEHOLDER_SECRETS = {
    "change-me-in-production",
    "replace-this-with-a-long-random-string",
    "",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "MindMap OS"
    ENV: Literal["development", "production", "test"] = "development"
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://mindmap:mindmap@postgres:5432/mindmap"

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- JWT ---
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 100
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _reject_insecure_production_config(self) -> "Settings":
        """Fail fast at process startup instead of silently serving traffic
        with a guessable JWT secret or wide-open CORS - a misconfiguration
        that would otherwise only surface as a security incident later."""
        if self.ENV != "production":
            return self

        if self.JWT_SECRET_KEY in _PLACEHOLDER_SECRETS or len(self.JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_SECRET_KEY is missing, a placeholder, or too short for ENV=production. "
                "Generate a real one: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )

        if "*" in self.cors_origins_list:
            raise ValueError(
                "CORS_ORIGINS cannot be '*' with ENV=production - list your real frontend "
                "origin(s) explicitly."
            )

        if any("localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origins_list):
            raise ValueError(
                "CORS_ORIGINS still points at localhost with ENV=production - set it to your "
                "real deployed frontend URL(s)."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
