"""OS-APOW Queue Package.

This package contains the work queue abstractions and implementations:
- IWorkQueue: Abstract interface for work queue operations
- GitHubIssueQueue: GitHub Issues implementation
"""

from src.queue.github_queue import GitHubIssueQueue
from src.queue.interfaces import IWorkQueue

__all__ = [
    "IWorkQueue",
    "GitHubIssueQueue",
]
