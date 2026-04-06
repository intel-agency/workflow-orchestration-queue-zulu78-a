"""
OS-APOW API Package
"""

from ..config import get_settings  # Re-export from config
from .deps import get_github_queue

__all__ = ["get_github_queue", "get_settings"]
