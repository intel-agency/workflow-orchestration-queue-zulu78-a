"""
OS-APOW Test Configuration

Pytest configuration and shared fixtures.
"""

import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from os_apow.config import Settings
from os_apow.models.work_item import TaskType, WorkItem, WorkItemStatus
from os_apow.services.queue import GitHubQueue


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing.

    Returns:
        Settings instance with test values.
    """
    return Settings(
        github_token="FAKE-KEY-FOR-TESTING-00000000",
        github_org="test-org",
        github_repo="test-repo",
        sentinel_bot_login="test-bot",
        webhook_secret="test-secret",
        webhook_port=8000,
        sentinel_id="test-sentinel-001",
        poll_interval_seconds=60,
        heartbeat_interval_seconds=300,
    )


@pytest.fixture
def sample_work_item() -> WorkItem:
    """Create a sample work item for testing.

    Returns:
        Sample WorkItem instance.
    """
    return WorkItem(
        id="12345",
        issue_number=42,
        source_url="https://github.com/test-org/test-repo/issues/42",
        context_body="Test issue body",
        target_repo_slug="test-org/test-repo",
        task_type=TaskType.IMPLEMENT,
        status=WorkItemStatus.QUEUED,
        node_id="I_test123",
    )


@pytest.fixture
def mock_github_queue(mock_settings: Settings) -> GitHubQueue:
    """Create a mock GitHub queue for testing.

    Args:
        mock_settings: Test settings.

    Returns:
        GitHubQueue instance with mock client.
    """
    return GitHubQueue(
        token=mock_settings.github_token,
        org=mock_settings.github_org,
        repo=mock_settings.github_repo,
    )


@pytest.fixture
def mock_httpx_response() -> MagicMock:
    """Create a mock HTTPX response.

    Returns:
        Mock response object.
    """
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {}
    response.text = ""
    return response


@pytest.fixture
async def mock_async_client() -> AsyncMock:
    """Create a mock async HTTP client.

    Returns:
        Mock AsyncClient instance.
    """
    client = AsyncMock()
    client.get = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: []))
    client.post = AsyncMock(return_value=MagicMock(status_code=201))
    client.delete = AsyncMock(return_value=MagicMock(status_code=204))
    client.aclose = AsyncMock()
    return client
