"""Unit tests for GitHubIssueQueue implementation.

These tests validate the GitHub Issues-backed work queue implementation.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.github_queue import GitHubIssueQueue


class TestGitHubIssueQueueInit:
    """Tests for GitHubIssueQueue initialization."""

    def test_init_with_parameters(self) -> None:
        """GitHubIssueQueue should accept token and repo_slug parameters."""
        queue = GitHubIssueQueue(token="test-token", repo_slug="owner/repo")
        assert queue._token == "test-token"
        assert queue._repo_slug == "owner/repo"

    def test_init_with_env_vars(self) -> None:
        """GitHubIssueQueue should read from environment variables."""
        with patch.dict(
            os.environ,
            {"GITHUB_TOKEN": "env-token", "GITHUB_REPO": "env-owner/env-repo"},
        ):
            queue = GitHubIssueQueue()
            assert queue._token == "env-token"
            assert queue._repo_slug == "env-owner/env-repo"

    def test_init_missing_token_raises_error(self) -> None:
        """GitHubIssueQueue should raise ValueError if token is missing."""
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match="GitHub token not provided"),
        ):
            GitHubIssueQueue(repo_slug="owner/repo")

    def test_init_missing_repo_slug_raises_error(self) -> None:
        """GitHubIssueQueue should raise ValueError if repo_slug is missing."""
        with (
            patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}, clear=True),
            pytest.raises(ValueError, match="Repository slug not provided"),
        ):
            GitHubIssueQueue(token="test-token")


class TestGitHubIssueQueueFetchQueuedItems:
    """Tests for fetch_queued_items method."""

    @pytest.fixture
    def queue(self) -> GitHubIssueQueue:
        """Fixture providing a GitHubIssueQueue instance with mocked client."""
        queue = GitHubIssueQueue(token="test-token", repo_slug="owner/repo")
        # Pre-set the client to a mock
        queue._client = MagicMock(spec=httpx.AsyncClient)
        return queue

    @pytest.fixture
    def mock_issues_response(self) -> list[dict]:
        """Fixture providing mock GitHub issues response."""
        return [
            {
                "id": 12345,
                "number": 1,
                "html_url": "https://github.com/owner/repo/issues/1",
                "body": "Test issue body",
                "title": "Test Issue",
                "node_id": "I_abc123",
                "labels": [
                    {"name": "agent:queued"},
                    {"name": "enhancement"},
                ],
            },
            {
                "id": 12346,
                "number": 2,
                "html_url": "https://github.com/owner/repo/issues/2",
                "body": "[Plan] Architecture design",
                "title": "[Plan] Design System",
                "node_id": "I_def456",
                "labels": [
                    {"name": "agent:queued"},
                    {"name": "agent:plan"},
                ],
            },
            {
                "id": 12347,
                "number": 3,
                "html_url": "https://github.com/owner/repo/issues/3",
                "body": "Fix the bug",
                "title": "Bug: Something broken",
                "node_id": "I_ghi789",
                "labels": [
                    {"name": "agent:queued"},
                    {"name": "bug"},
                ],
            },
        ]

    @pytest.mark.asyncio
    async def test_fetch_queued_items_returns_list(
        self, queue: GitHubIssueQueue, mock_issues_response: list[dict]
    ) -> None:
        """fetch_queued_items should return a list of WorkItems."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issues_response
        queue._client.get = AsyncMock(return_value=mock_response)

        items = await queue.fetch_queued_items()
        assert isinstance(items, list)
        assert all(isinstance(item, WorkItem) for item in items)

    @pytest.mark.asyncio
    async def test_fetch_queued_items_maps_to_work_items(
        self, queue: GitHubIssueQueue, mock_issues_response: list[dict]
    ) -> None:
        """fetch_queued_items should correctly map GitHub issues to WorkItems."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issues_response
        queue._client.get = AsyncMock(return_value=mock_response)

        items = await queue.fetch_queued_items()
        assert len(items) == 3

        # Check first item (IMPLEMENT)
        assert items[0].id == "12345"
        assert items[0].source_url == "https://github.com/owner/repo/issues/1"
        assert items[0].context_body == "Test issue body"
        assert items[0].target_repo_slug == "owner/repo"
        assert items[0].task_type == TaskType.IMPLEMENT
        assert items[0].status == WorkItemStatus.QUEUED
        assert items[0].metadata["issue_number"] == 1

    @pytest.mark.asyncio
    async def test_fetch_queued_items_detects_plan_type(
        self, queue: GitHubIssueQueue, mock_issues_response: list[dict]
    ) -> None:
        """fetch_queued_items should detect PLAN task type from labels/title."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issues_response
        queue._client.get = AsyncMock(return_value=mock_response)

        items = await queue.fetch_queued_items()
        # Second item should be PLAN
        assert items[1].task_type == TaskType.PLAN

    @pytest.mark.asyncio
    async def test_fetch_queued_items_detects_bugfix_type(
        self, queue: GitHubIssueQueue, mock_issues_response: list[dict]
    ) -> None:
        """fetch_queued_items should detect BUGFIX task type from labels."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issues_response
        queue._client.get = AsyncMock(return_value=mock_response)

        items = await queue.fetch_queued_items()
        # Third item should be BUGFIX
        assert items[2].task_type == TaskType.BUGFIX

    @pytest.mark.asyncio
    async def test_fetch_queued_items_empty_response(self, queue: GitHubIssueQueue) -> None:
        """fetch_queued_items should return empty list when no issues found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        queue._client.get = AsyncMock(return_value=mock_response)

        items = await queue.fetch_queued_items()
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_queued_items_handles_api_error(self, queue: GitHubIssueQueue) -> None:
        """fetch_queued_items should return empty list on API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        queue._client.get = AsyncMock(return_value=mock_response)

        items = await queue.fetch_queued_items()
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_queued_items_raises_on_rate_limit(self, queue: GitHubIssueQueue) -> None:
        """fetch_queued_items should raise HTTPStatusError on rate limit."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=mock_response
        )
        queue._client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await queue.fetch_queued_items()


class TestGitHubIssueQueueUpdateItemStatus:
    """Tests for update_item_status method."""

    @pytest.fixture
    def queue(self) -> GitHubIssueQueue:
        """Fixture providing a GitHubIssueQueue instance with mocked client."""
        queue = GitHubIssueQueue(token="test-token", repo_slug="owner/repo")
        queue._client = MagicMock(spec=httpx.AsyncClient)
        return queue

    @pytest.fixture
    def sample_item(self) -> WorkItem:
        """Fixture providing a sample work item."""
        return WorkItem(
            id="12345",
            source_url="https://github.com/owner/repo/issues/1",
            context_body="Test issue",
            target_repo_slug="owner/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            metadata={"issue_number": 1, "node_id": "I_abc123"},
        )

    @pytest.mark.asyncio
    async def test_update_item_status_returns_bool(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should return a boolean."""
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        queue._client.delete = AsyncMock(return_value=mock_delete_response)
        queue._client.post = AsyncMock(return_value=mock_add_response)

        result = await queue.update_item_status(sample_item, WorkItemStatus.IN_PROGRESS)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_update_item_status_success(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should return True on successful update."""
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        queue._client.delete = AsyncMock(return_value=mock_delete_response)
        queue._client.post = AsyncMock(return_value=mock_add_response)

        result = await queue.update_item_status(sample_item, WorkItemStatus.IN_PROGRESS)
        assert result is True

    @pytest.mark.asyncio
    async def test_update_item_status_removes_old_label(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should remove the old status label."""
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        queue._client.delete = AsyncMock(return_value=mock_delete_response)
        queue._client.post = AsyncMock(return_value=mock_add_response)

        await queue.update_item_status(sample_item, WorkItemStatus.SUCCESS)

        # Verify delete was called with old label
        queue._client.delete.assert_called_once()
        call_args = queue._client.delete.call_args
        assert "agent:queued" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_item_status_adds_new_label(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should add the new status label."""
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        queue._client.delete = AsyncMock(return_value=mock_delete_response)
        queue._client.post = AsyncMock(return_value=mock_add_response)

        await queue.update_item_status(sample_item, WorkItemStatus.SUCCESS)

        # Verify post was called with new label
        queue._client.post.assert_called_once()
        call_args = queue._client.post.call_args
        assert call_args[1]["json"]["labels"] == ["agent:success"]

    @pytest.mark.asyncio
    async def test_update_item_status_missing_issue_number(self, queue: GitHubIssueQueue) -> None:
        """update_item_status should return False if issue_number is missing."""
        item = WorkItem(
            id="12345",
            source_url="https://github.com/owner/repo/issues/1",
            context_body="Test issue",
            target_repo_slug="owner/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            metadata={},  # No issue_number
        )

        result = await queue.update_item_status(item, WorkItemStatus.IN_PROGRESS)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_item_status_handles_api_error(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should return False on API error."""
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_add_response = MagicMock()
        mock_add_response.status_code = 500
        mock_add_response.text = "Internal Server Error"
        queue._client.delete = AsyncMock(return_value=mock_delete_response)
        queue._client.post = AsyncMock(return_value=mock_add_response)

        result = await queue.update_item_status(sample_item, WorkItemStatus.IN_PROGRESS)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_item_status_handles_delete_error(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should handle errors when removing old label."""
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 500  # Error on delete
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        queue._client.delete = AsyncMock(return_value=mock_delete_response)
        queue._client.post = AsyncMock(return_value=mock_add_response)

        result = await queue.update_item_status(sample_item, WorkItemStatus.SUCCESS)
        # Should still succeed if add works
        assert result is True

    @pytest.mark.asyncio
    async def test_update_item_status_handles_delete_exception(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should handle exceptions when removing old label."""
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        queue._client.delete = AsyncMock(side_effect=httpx.HTTPError("Network error"))
        queue._client.post = AsyncMock(return_value=mock_add_response)

        result = await queue.update_item_status(sample_item, WorkItemStatus.SUCCESS)
        # Should still succeed if add works
        assert result is True

    @pytest.mark.asyncio
    async def test_update_item_status_handles_post_exception(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should return False on post exception."""
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        queue._client.delete = AsyncMock(return_value=mock_delete_response)
        queue._client.post = AsyncMock(side_effect=httpx.HTTPError("Network error"))

        result = await queue.update_item_status(sample_item, WorkItemStatus.IN_PROGRESS)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_item_status_same_status(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """update_item_status should skip delete when status unchanged."""
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        queue._client.delete = AsyncMock()
        queue._client.post = AsyncMock(return_value=mock_add_response)

        # Update to same status
        result = await queue.update_item_status(sample_item, WorkItemStatus.QUEUED)

        # Delete should not be called (same status)
        queue._client.delete.assert_not_called()
        assert result is True


class TestGitHubIssueQueueClose:
    """Tests for close method."""

    @pytest.fixture
    def queue(self) -> GitHubIssueQueue:
        """Fixture providing a GitHubIssueQueue instance."""
        queue = GitHubIssueQueue(token="test-token", repo_slug="owner/repo")
        queue._client = AsyncMock(spec=httpx.AsyncClient)
        return queue

    @pytest.mark.asyncio
    async def test_close_releases_client(self, queue: GitHubIssueQueue) -> None:
        """close should release the HTTP client."""
        assert queue._client is not None

        await queue.close()
        assert queue._client is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self, queue: GitHubIssueQueue) -> None:
        """close should be idempotent (can be called multiple times)."""
        await queue.close()
        await queue.close()  # Should not raise


class TestGitHubIssueQueueAddComment:
    """Tests for add_comment method."""

    @pytest.fixture
    def queue(self) -> GitHubIssueQueue:
        """Fixture providing a GitHubIssueQueue instance with mocked client."""
        queue = GitHubIssueQueue(token="test-token", repo_slug="owner/repo")
        queue._client = MagicMock(spec=httpx.AsyncClient)
        return queue

    @pytest.fixture
    def sample_item(self) -> WorkItem:
        """Fixture providing a sample work item."""
        return WorkItem(
            id="12345",
            source_url="https://github.com/owner/repo/issues/1",
            context_body="Test issue",
            target_repo_slug="owner/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            metadata={"issue_number": 1, "node_id": "I_abc123"},
        )

    @pytest.mark.asyncio
    async def test_add_comment_returns_bool(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """add_comment should return a boolean."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        queue._client.post = AsyncMock(return_value=mock_response)

        result = await queue.add_comment(sample_item, "Test comment")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_add_comment_success(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """add_comment should return True on successful post."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        queue._client.post = AsyncMock(return_value=mock_response)

        result = await queue.add_comment(sample_item, "Test comment")
        assert result is True

    @pytest.mark.asyncio
    async def test_add_comment_scrubs_secrets(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """add_comment should scrub secrets by default."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        queue._client.post = AsyncMock(return_value=mock_response)

        # Use synthetic test-safe format
        await queue.add_comment(sample_item, "Token: ghp_abcdefghijklmnopqrstuvwxyz0123456789")

        # Verify the comment was scrubbed
        call_args = queue._client.post.call_args
        body = call_args[1]["json"]["body"]
        assert "ghp_" not in body
        assert "***REDACTED***" in body

    @pytest.mark.asyncio
    async def test_add_comment_skip_scrub(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """add_comment should skip scrubbing when scrub=False."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        queue._client.post = AsyncMock(return_value=mock_response)

        await queue.add_comment(sample_item, "Test comment", scrub=False)

        # Verify the comment was not scrubbed
        call_args = queue._client.post.call_args
        body = call_args[1]["json"]["body"]
        assert body == "Test comment"

    @pytest.mark.asyncio
    async def test_add_comment_missing_issue_number(self, queue: GitHubIssueQueue) -> None:
        """add_comment should return False if issue_number is missing."""
        item = WorkItem(
            id="12345",
            source_url="https://github.com/owner/repo/issues/1",
            context_body="Test issue",
            target_repo_slug="owner/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            metadata={},  # No issue_number
        )

        result = await queue.add_comment(item, "Test comment")
        assert result is False

    @pytest.mark.asyncio
    async def test_add_comment_handles_api_error(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """add_comment should return False on API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        queue._client.post = AsyncMock(return_value=mock_response)

        result = await queue.add_comment(sample_item, "Test comment")
        assert result is False

    @pytest.mark.asyncio
    async def test_add_comment_handles_exception(
        self, queue: GitHubIssueQueue, sample_item: WorkItem
    ) -> None:
        """add_comment should return False on exception."""
        queue._client.post = AsyncMock(side_effect=httpx.HTTPError("Network error"))

        result = await queue.add_comment(sample_item, "Test comment")
        assert result is False


class TestModuleImports:
    """Tests for module-level imports."""

    def test_import_from_queue_init(self) -> None:
        """GitHubIssueQueue should be importable from queue/__init__.py."""
        from src.queue import GitHubIssueQueue  # noqa: F401

        # If import succeeds, test passes
        assert True

    def test_import_from_github_queue_module(self) -> None:
        """GitHubIssueQueue should be importable from github_queue.py directly."""
        from src.queue.github_queue import GitHubIssueQueue as ImportedQueue

        assert ImportedQueue is GitHubIssueQueue
