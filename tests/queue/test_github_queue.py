"""Tests for the GitHub Queue implementation."""

import pytest

from src.queue.github_queue import GitHubQueue, ITaskQueue


class TestITaskQueue:
    """Tests for the ITaskQueue abstract interface."""

    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            ITaskQueue()

    def test_github_queue_is_itask_queue(self):
        queue = GitHubQueue(token="FAKE-KEY-FOR-TESTING-00000000")
        assert isinstance(queue, ITaskQueue)


class TestGitHubQueue:
    """Tests for the GitHubQueue implementation."""

    def _make_queue(self):
        return GitHubQueue(
            token="FAKE-KEY-FOR-TESTING-00000000",
            org="test-org",
            repo="test-repo",
        )

    def test_init_stores_config(self):
        queue = self._make_queue()
        assert queue.org == "test-org"
        assert queue.repo == "test-repo"
        assert queue.token == "FAKE-KEY-FOR-TESTING-00000000"

    def test_headers_set(self):
        queue = self._make_queue()
        assert "Authorization" in queue.headers
        assert queue.headers["Accept"] == "application/vnd.github.v3+json"

    def test_repo_api_url(self):
        queue = self._make_queue()
        url = queue._repo_api_url("owner/repo")
        assert url == "https://api.github.com/repos/owner/repo"

    @pytest.mark.asyncio
    async def test_close(self):
        queue = self._make_queue()
        await queue.close()
        # Should not raise

    @pytest.mark.asyncio
    async def test_fetch_queued_empty_without_config(self):
        queue = GitHubQueue(token="FAKE-KEY-FOR-TESTING-00000000")
        result = await queue.fetch_queued_tasks()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_queued_empty_without_org(self):
        queue = GitHubQueue(token="FAKE-KEY-FOR-TESTING-00000000", repo="test")
        result = await queue.fetch_queued_tasks()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_queued_empty_without_repo(self):
        queue = GitHubQueue(token="FAKE-KEY-FOR-TESTING-00000000", org="test")
        result = await queue.fetch_queued_tasks()
        assert result == []
