"""
OS-APOW Configuration Module

Pydantic Settings-based configuration management using environment variables.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables with the
    prefix OS_APOW_ (e.g., OS_APOW_GITHUB_TOKEN).
    """

    model_config = SettingsConfigDict(
        env_prefix="OS_APOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GitHub Configuration
    github_token: str = Field(..., description="GitHub personal access token or app token")
    github_org: str = Field(default="", description="GitHub organization name")
    github_repo: str = Field(default="", description="Target repository (owner/repo format)")
    sentinel_bot_login: str = Field(
        default="", description="Bot account login for distributed locking"
    )

    # Webhook Configuration
    webhook_secret: str = Field(
        default="", description="HMAC secret for webhook signature validation"
    )
    webhook_port: int = Field(default=8000, description="Port for webhook receiver")

    # Sentinel Configuration
    sentinel_id: str = Field(
        default="sentinel-001", description="Unique identifier for this sentinel instance"
    )
    poll_interval_seconds: int = Field(
        default=60, description="Interval between GitHub API polling cycles"
    )
    heartbeat_interval_seconds: int = Field(
        default=300, description="Interval between heartbeat comments (5 minutes)"
    )

    # DevContainer Configuration
    devcontainer_network: str = Field(
        default="os-apow-network", description="Docker network for worker isolation"
    )
    devcontainer_cpu_limit: float = Field(default=2.0, description="CPU limit per worker container")
    devcontainer_memory_limit: str = Field(
        default="4g", description="Memory limit per worker container"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_format: str = Field(default="json", description="Log format (json or text)")


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
