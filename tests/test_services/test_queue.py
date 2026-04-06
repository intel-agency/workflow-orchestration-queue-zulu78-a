"""
Tests for OS-APOW Queue Service
"""

from unittest.mock import MagicMock, patch

import pytest

from os_apow.models.work_item import WorkItem
from os_apow.services.queue import GitHubQueue, ITaskQueue


class TestITaskQueue:
    """Tests for the abstract ITaskQueue interface."""

    def test_cannot_instantiate_abstract(self) -> None:
        """Test that ITaskQueue cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ITaskQueue()  # type: ignore


class TestGitHubQueue:
    """Tests for GitHub queue implementation."""

    @pytest.fixture
    def queue(self, mock_settings) -> GitHubQueue:
        """Create a GitHubQueue instance for testing."""
        return GitHubQueue(
            token=mock_settings.github_token,
            org=mock_settings.github_org,
            repo=mock_settings.github_repo,
        )

    @pytest.mark.asyncio
    async def test_close_releases_client(self, queue: GitHubQueue) -> None:
        """Test that close releases the HTTP client."""
        await queue.close()
        # Should not raise an error

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_requires_org_repo(self) -> None:
        """Test that fetch requires org and repo to be set."""
        queue = GitHubQueue(token="test-token", org="", repo="")
        tasks = await queue.fetch_queued_tasks()
        assert tasks == []

    @pytest.mark.asyncio
    async def test_add_to_queue_success(
        self, queue: GitHubQueue, sample_work_item: WorkItem
    ) -> None:
        """Test successful add to queue."""
        with patch.object(queue._client, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_post.return_value = mock_response

            result = await queue.add_to_queue(sample_work_item)

            assert result is True
            mock_post.assert_called_once()


class TestCredentialScrubbing:
    """Tests for credential scrubbing functionality."""

    def test_scrub_github_pat(self) -> None:
        """Test that GitHub PAT patterns are scrubbed."""
        from os_apow.models.work_item import scrub_secrets

        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "***REDACTED***" in result

    def test_scrub_bearer_token(self) -> None:
        """Test that Bearer tokens are scrubbed."""
        from os_apow.models.work_item import scrub_secrets

        text = "Authorization: Bearer abc123xyz789"
        result = scrub_secrets(text)
        assert "Bearer" not in result or "***REDACTED***" in result

    def test_scrub_preserves_normal_text(self) -> None:
        """Test that normal text is preserved."""
        from os_apow.models.work_item import scrub_secrets

        text = "This is normal text without secrets"
        result = scrub_secrets(text)
        assert result == text

    def test_custom_replacement(self) -> None:
        """Test custom replacement string."""
        from os_apow.models.work_item import scrub_secrets

        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        result = scrub_secrets(text, replacement="[HIDDEN]")
        assert "[HIDDEN]" in result
