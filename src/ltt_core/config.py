"""
LTT Cloud -- Central configuration.

All sensitive values (DATABASE_URL, REDIS_URL, etc.) are read exclusively
from environment variables.  In local development they come from the
gitignored .env file; in CI from GitHub Actions Secrets; in production
from Kubernetes Secret objects mounted as env vars.

Required env vars (must be set in staging/prod, see .env.example):
  DATABASE_URL   -- full DB connection string (PostgreSQL or MSSQL)
  REDIS_URL      -- full Redis connection string
  ENVIRONMENT    -- "dev" | "staging" | "prod"

Optional / safe defaults:
  BRIGHTWAY_PROJECT -- Brightway project name (default: LTT_P2X)
  JWT_SECRET_KEY    -- signing key for auth tokens (required in prod)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Non-sensitive constants (safe to keep in source code)
# ---------------------------------------------------------------------------
RWTH_BLUE: str = "#00549F"
LTT_GREEN: str = "#A2AD00"


class Settings(BaseSettings):
    """Single source of truth for all runtime configuration.

    Sensitive fields have NO defaults -- the application will refuse to
    start if they are missing (fail-fast).
    """

    model_config = SettingsConfigDict(
        # In development the .env sitting next to the project root is loaded
        # automatically.  In CI/K8s the real values come from the environment.
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- required, sensitive ------------------------------------------------
    DATABASE_URL: str
    REDIS_URL: str

    # -- sensitive, optional in dev (required in staging/prod) --------------
    JWT_SECRET_KEY: str = ""

    # -- required, non-sensitive --------------------------------------------
    ENVIRONMENT: str = "dev"

    # -- optional, non-sensitive --------------------------------------------
    BRIGHTWAY_PROJECT: str = "LTT_P2X"
    API_URL: str = "http://localhost:8000"

    # -- derived convenience properties (not from env) ----------------------
    @property
    def rwth_blue(self) -> str:
        return RWTH_BLUE

    @property
    def ltt_green(self) -> str:
        return LTT_GREEN

    # -- validation ---------------------------------------------------------
    @field_validator("ENVIRONMENT")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        allowed = {"dev", "staging", "prod"}
        if v not in allowed:
            raise ValueError(
                f"ENVIRONMENT must be one of {allowed}, got '{v}'"
            )
        return v

    def check_production_secrets(self) -> None:
        """Call at startup to enforce secrets in non-dev environments."""
        if self.ENVIRONMENT in ("staging", "prod") and not self.JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY is required in staging/prod environments"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Usage everywhere in the codebase:
        from ltt_core.config import get_settings
        settings = get_settings()
        db_url = settings.DATABASE_URL

    In tests, clear the cache to inject overrides:
        get_settings.cache_clear()
    """
    return Settings()