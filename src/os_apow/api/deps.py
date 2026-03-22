"""
OS-APOW API Dependency Injection

FastAPI dependency providers for settings, queue, and clients.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ..config import Settings, get_settings
from ..services.queue import GitHubQueue


@lru_cache
def get_github_queue(settings: Annotated[Settings, Depends(get_settings)]) -> GitHubQueue:
    """Get a cached GitHub queue instance.

    Args:
        settings: Application settings.

    Returns:
        GitHubQueue instance.
    """
    return GitHubQueue(
        token=settings.github_token,
        org=settings.github_org,
        repo=settings.github_repo,
    )
