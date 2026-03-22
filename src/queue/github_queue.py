"""OS-APOW GitHub Issue Queue Implementation.

GitHub Issues-backed work queue that implements the IWorkQueue interface.
This allows the orchestrator to use GitHub Issues as the work queue provider.

See: OS-APOW Plan Review, I-1 / R-3
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import httpx

from src.models.work_item import (
    TaskType,
    WorkItem,
    WorkItemStatus,
    scrub_secrets,
)
from src.queue.interfaces import IWorkQueue

if TYPE_CHECKING:
    pass

logger = logging.getLogger("OS-APOW")


class GitHubIssueQueue(IWorkQueue):
    """GitHub Issues-backed work queue implementation.

    This class implements the IWorkQueue interface using GitHub Issues as the
    backing store. Issues labeled with 'agent:queued' are fetched as work items,
    and status updates are reflected as label changes.

    Attributes:
        token: GitHub personal access token for API authentication.
        repo_slug: Target repository in 'owner/repo' format.

    Example:
        >>> queue = GitHubIssueQueue(token="ghp_xxx", repo_slug="owner/repo")
        >>> items = await queue.fetch_queued_items()
        >>> for item in items:
        ...     print(f"Processing issue #{item.metadata.get('issue_number')}")
    """

    def __init__(
        self,
        token: str | None = None,
        repo_slug: str | None = None,
    ) -> None:
        """Initialize the GitHub Issue Queue.

        Args:
            token: GitHub personal access token. If not provided, reads from
                GITHUB_TOKEN environment variable.
            repo_slug: Target repository in 'owner/repo' format. If not provided,
                reads from GITHUB_REPO environment variable.

        Raises:
            ValueError: If token or repo_slug are not provided and not found
                in environment variables.
        """
        self._token = token or os.environ.get("GITHUB_TOKEN")
        self._repo_slug = repo_slug or os.environ.get("GITHUB_REPO")

        if not self._token:
            msg = "GitHub token not provided. Set GITHUB_TOKEN environment variable."
            raise ValueError(msg)
        if not self._repo_slug:
            msg = "Repository slug not provided. Set GITHUB_REPO environment variable."
            raise ValueError(msg)

        self._headers = {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self._client: httpx.AsyncClient | None = None

    @property
    def _api_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self._headers,
                timeout=30.0,
            )
        return self._client

    def _repo_api_url(self) -> str:
        """Get the GitHub API URL for the configured repository."""
        return f"https://api.github.com/repos/{self._repo_slug}"

    async def fetch_queued_items(self) -> list[WorkItem]:
        """Fetch all issues labeled 'agent:queued' from the repository.

        Returns:
            List of WorkItem objects representing queued GitHub Issues.

        Raises:
            httpx.HTTPStatusError: If the GitHub API returns an error.
        """
        url = f"{self._repo_api_url()}/issues"
        params = {
            "labels": WorkItemStatus.QUEUED.value,
            "state": "open",
        }

        response = await self._api_client.get(url, params=params)

        # Handle rate limiting
        if response.status_code in (403, 429):
            logger.warning("GitHub API rate limit hit. Status: %s", response.status_code)
            response.raise_for_status()

        if response.status_code != 200:
            logger.error(
                "GitHub API error: %s - %s",
                response.status_code,
                response.text[:200],
            )
            return []

        issues = response.json()
        work_items = []

        for issue in issues:
            labels = [label["name"] for label in issue.get("labels", [])]

            # Determine task type from labels or title
            task_type = TaskType.IMPLEMENT
            if "agent:plan" in labels or "[Plan]" in issue.get("title", ""):
                task_type = TaskType.PLAN
            elif "bug" in labels:
                task_type = TaskType.BUGFIX

            # Extract repo slug from issue URL
            html_url = issue.get("html_url", "")
            url_parts = html_url.split("/")
            issue_repo_slug = "/".join(url_parts[3:5]) if len(url_parts) >= 5 else self._repo_slug

            work_items.append(
                WorkItem(
                    id=str(issue["id"]),
                    source_url=html_url,
                    context_body=issue.get("body") or "",
                    target_repo_slug=issue_repo_slug,
                    task_type=task_type,
                    status=WorkItemStatus.QUEUED,
                    metadata={
                        "issue_number": issue["number"],
                        "node_id": issue.get("node_id"),
                        "title": issue.get("title"),
                        "labels": labels,
                    },
                )
            )

        logger.info("Fetched %d queued items from GitHub", len(work_items))
        return work_items

    async def update_item_status(self, item: WorkItem, new_status: WorkItemStatus) -> bool:
        """Update the status of a work item by managing GitHub labels.

        This removes the old status label and adds the new one.

        Args:
            item: The WorkItem to update.
            new_status: The new status to set.

        Returns:
            True if the update was successful, False otherwise.
        """
        issue_number = item.metadata.get("issue_number")
        if not issue_number:
            logger.error("Cannot update item without issue_number in metadata")
            return False

        base_url = f"{self._repo_api_url()}/issues/{issue_number}"
        labels_url = f"{base_url}/labels"

        # Remove the old status label (if it exists and is different)
        if item.status != new_status:
            try:
                delete_response = await self._api_client.delete(f"{labels_url}/{item.status.value}")
                if delete_response.status_code not in (200, 204, 404):
                    logger.warning("Failed to remove old label: %s", delete_response.status_code)
            except httpx.HTTPError as e:
                logger.warning("Error removing old label: %s", e)

        # Add the new status label
        try:
            add_response = await self._api_client.post(
                labels_url,
                json={"labels": [new_status.value]},
            )
            if add_response.status_code in (200, 201):
                logger.info("Updated issue #%s status to %s", issue_number, new_status.value)
                return True
            logger.error(
                "Failed to add new label: %s - %s",
                add_response.status_code,
                add_response.text[:200],
            )
            return False
        except httpx.HTTPError as e:
            logger.error("Error adding new label: %s", e)
            return False

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("GitHub Issue Queue closed")

    async def add_comment(self, item: WorkItem, comment: str, *, scrub: bool = True) -> bool:
        """Add a comment to the GitHub issue.

        Args:
            item: The WorkItem to comment on.
            comment: The comment body to post.
            scrub: Whether to scrub secrets from the comment (default: True).

        Returns:
            True if the comment was posted successfully, False otherwise.
        """
        issue_number = item.metadata.get("issue_number")
        if not issue_number:
            logger.error("Cannot add comment without issue_number in metadata")
            return False

        comment_url = f"{self._repo_api_url()}/issues/{issue_number}/comments"
        body = scrub_secrets(comment) if scrub else comment

        try:
            response = await self._api_client.post(
                comment_url,
                json={"body": body},
            )
            if response.status_code in (200, 201):
                logger.info("Added comment to issue #%s", issue_number)
                return True
            logger.error(
                "Failed to add comment: %s - %s",
                response.status_code,
                response.text[:200],
            )
            return False
        except httpx.HTTPError as e:
            logger.error("Error adding comment: %s", e)
            return False
