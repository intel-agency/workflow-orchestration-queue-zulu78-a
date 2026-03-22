"""
OS-APOW GitHub Client

HTTPX-based GitHub API wrapper with connection pooling and
rate limit handling.
"""

import logging
from typing import Any

import httpx

from ..config import get_settings

logger = logging.getLogger("os_apow.github_client")


class GitHubClient:
    """GitHub API client with connection pooling.

    Provides a high-level interface for GitHub REST API operations
    used by both the Notifier and Sentinel services.
    """

    def __init__(self, token: str | None = None):
        """Initialize the GitHub client.

        Args:
            token: GitHub token. If not provided, uses settings.
        """
        settings = get_settings()
        self.token = token or settings.github_token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client connection pool."""
        await self._client.aclose()

    def _repo_url(self, repo_slug: str) -> str:
        """Build API URL for a repository.

        Args:
            repo_slug: Repository in owner/repo format.

        Returns:
            Full API URL.
        """
        return f"https://api.github.com/repos/{repo_slug}"

    async def get_issue(self, repo_slug: str, issue_number: int) -> dict[str, Any]:
        """Fetch a single issue.

        Args:
            repo_slug: Repository in owner/repo format.
            issue_number: Issue number.

        Returns:
            Issue data as dictionary.
        """
        url = f"{self._repo_url(repo_slug)}/issues/{issue_number}"
        response = await self._client.get(url)
        response.raise_for_status()
        return response.json()

    async def add_labels(
        self, repo_slug: str, issue_number: int, labels: list[str]
    ) -> dict[str, Any]:
        """Add labels to an issue.

        Args:
            repo_slug: Repository in owner/repo format.
            issue_number: Issue number.
            labels: List of label names to add.

        Returns:
            Updated labels data.
        """
        url = f"{self._repo_url(repo_slug)}/issues/{issue_number}/labels"
        response = await self._client.post(url, json={"labels": labels})
        response.raise_for_status()
        return response.json()

    async def remove_label(self, repo_slug: str, issue_number: int, label: str) -> dict[str, Any]:
        """Remove a label from an issue.

        Args:
            repo_slug: Repository in owner/repo format.
            issue_number: Issue number.
            label: Label name to remove.

        Returns:
            Response data.
        """
        url = f"{self._repo_url(repo_slug)}/issues/{issue_number}/labels/{label}"
        response = await self._client.delete(url)
        # 404 is acceptable (label already removed)
        if response.status_code not in (200, 204, 404):
            response.raise_for_status()
        return response.json() if response.content else {}

    async def create_comment(self, repo_slug: str, issue_number: int, body: str) -> dict[str, Any]:
        """Create a comment on an issue.

        Args:
            repo_slug: Repository in owner/repo format.
            issue_number: Issue number.
            body: Comment body text.

        Returns:
            Created comment data.
        """
        url = f"{self._repo_url(repo_slug)}/issues/{issue_number}/comments"
        response = await self._client.post(url, json={"body": body})
        response.raise_for_status()
        return response.json()

    async def add_assignees(
        self, repo_slug: str, issue_number: int, assignees: list[str]
    ) -> dict[str, Any]:
        """Add assignees to an issue.

        Args:
            repo_slug: Repository in owner/repo format.
            issue_number: Issue number.
            assignees: List of GitHub usernames to assign.

        Returns:
            Updated issue data.
        """
        url = f"{self._repo_url(repo_slug)}/issues/{issue_number}/assignees"
        response = await self._client.post(url, json={"assignees": assignees})
        response.raise_for_status()
        return response.json()

    async def list_issues(
        self, repo_slug: str, labels: list[str] | None = None, state: str = "open"
    ) -> list[dict[str, Any]]:
        """List issues in a repository.

        Args:
            repo_slug: Repository in owner/repo format.
            labels: Filter by labels.
            state: Issue state (open, closed, all).

        Returns:
            List of issue data.
        """
        url = f"{self._repo_url(repo_slug)}/issues"
        params: dict[str, Any] = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()
