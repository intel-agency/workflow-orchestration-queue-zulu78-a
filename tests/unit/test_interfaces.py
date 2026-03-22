"""Unit tests for IWorkQueue abstract interface.

These tests validate the abstract interface definition for work queue operations.
"""

from __future__ import annotations

import pytest

from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.interfaces import IWorkQueue


class MockWorkQueue(IWorkQueue):
    """Mock implementation of IWorkQueue for testing."""

    def __init__(self) -> None:
        """Initialize mock queue with empty items list."""
        self._items: list[WorkItem] = []
        self._closed = False

    async def fetch_queued_items(self) -> list[WorkItem]:
        """Return the list of queued items."""
        return [item for item in self._items if item.status == WorkItemStatus.QUEUED]

    async def update_item_status(self, item: WorkItem, new_status: WorkItemStatus) -> bool:
        """Update item status in the list."""
        for i, existing_item in enumerate(self._items):
            if existing_item.id == item.id:
                self._items[i] = WorkItem(
                    id=item.id,
                    source_url=item.source_url,
                    context_body=item.context_body,
                    target_repo_slug=item.target_repo_slug,
                    task_type=item.task_type,
                    status=new_status,
                    metadata=item.metadata,
                )
                return True
        return False

    async def close(self) -> None:
        """Mark queue as closed."""
        self._closed = True

    def add_item(self, item: WorkItem) -> None:
        """Add an item to the mock queue."""
        self._items.append(item)


class TestIWorkQueueInterface:
    """Tests for IWorkQueue interface compliance."""

    @pytest.fixture
    def mock_queue(self) -> MockWorkQueue:
        """Fixture providing a mock work queue."""
        return MockWorkQueue()

    @pytest.fixture
    def sample_work_item(self) -> WorkItem:
        """Fixture providing a sample work item."""
        return WorkItem(
            id="test-1",
            source_url="https://github.com/owner/repo/issues/1",
            context_body="Test task",
            target_repo_slug="owner/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            metadata={"issue_number": 1},
        )

    @pytest.mark.asyncio
    async def test_fetch_queued_items_returns_list(self, mock_queue: MockWorkQueue) -> None:
        """fetch_queued_items should return a list of WorkItems."""
        items = await mock_queue.fetch_queued_items()
        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_fetch_queued_items_returns_queued_items(
        self, mock_queue: MockWorkQueue, sample_work_item: WorkItem
    ) -> None:
        """fetch_queued_items should return only queued items."""
        mock_queue.add_item(sample_work_item)

        # Add an in-progress item
        in_progress_item = WorkItem(
            id="test-2",
            source_url="https://github.com/owner/repo/issues/2",
            context_body="In progress task",
            target_repo_slug="owner/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.IN_PROGRESS,
        )
        mock_queue.add_item(in_progress_item)

        items = await mock_queue.fetch_queued_items()
        assert len(items) == 1
        assert items[0].id == "test-1"
        assert items[0].status == WorkItemStatus.QUEUED

    @pytest.mark.asyncio
    async def test_fetch_queued_items_empty_queue(self, mock_queue: MockWorkQueue) -> None:
        """fetch_queued_items should return empty list when no items queued."""
        items = await mock_queue.fetch_queued_items()
        assert items == []

    @pytest.mark.asyncio
    async def test_update_item_status_returns_bool(
        self, mock_queue: MockWorkQueue, sample_work_item: WorkItem
    ) -> None:
        """update_item_status should return a boolean."""
        mock_queue.add_item(sample_work_item)
        result = await mock_queue.update_item_status(sample_work_item, WorkItemStatus.IN_PROGRESS)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_update_item_status_success(
        self, mock_queue: MockWorkQueue, sample_work_item: WorkItem
    ) -> None:
        """update_item_status should return True on successful update."""
        mock_queue.add_item(sample_work_item)
        result = await mock_queue.update_item_status(sample_work_item, WorkItemStatus.IN_PROGRESS)
        assert result is True

    @pytest.mark.asyncio
    async def test_update_item_status_updates_status(
        self, mock_queue: MockWorkQueue, sample_work_item: WorkItem
    ) -> None:
        """update_item_status should update the item status."""
        mock_queue.add_item(sample_work_item)
        await mock_queue.update_item_status(sample_work_item, WorkItemStatus.SUCCESS)

        # Verify the status was updated
        items = await mock_queue.fetch_queued_items()
        assert len(items) == 0  # Item no longer queued

    @pytest.mark.asyncio
    async def test_update_item_status_not_found(
        self, mock_queue: MockWorkQueue, sample_work_item: WorkItem
    ) -> None:
        """update_item_status should return False if item not found."""
        # Don't add the item to the queue
        result = await mock_queue.update_item_status(sample_work_item, WorkItemStatus.IN_PROGRESS)
        assert result is False

    @pytest.mark.asyncio
    async def test_close_is_callable(self, mock_queue: MockWorkQueue) -> None:
        """close method should be callable."""
        await mock_queue.close()
        assert mock_queue._closed is True

    @pytest.mark.asyncio
    async def test_close_default_implementation(self) -> None:
        """Default close implementation should do nothing (no exception)."""

        class MinimalQueue(IWorkQueue):
            async def fetch_queued_items(self) -> list[WorkItem]:
                return []

            async def update_item_status(self, item: WorkItem, new_status: WorkItemStatus) -> bool:
                return True

        queue = MinimalQueue()
        # Should not raise
        await queue.close()


class TestIWorkQueueIsAbstract:
    """Tests verifying IWorkQueue is properly abstract."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """IWorkQueue should not be instantiable directly."""
        with pytest.raises(TypeError):
            IWorkQueue()  # type: ignore[abstract]

    def test_subclass_must_implement_fetch_queued_items(self) -> None:
        """Subclass must implement fetch_queued_items."""

        class IncompleteQueue(IWorkQueue):
            async def update_item_status(self, item: WorkItem, new_status: WorkItemStatus) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteQueue()  # type: ignore[abstract]

    def test_subclass_must_implement_update_item_status(self) -> None:
        """Subclass must implement update_item_status."""

        class IncompleteQueue(IWorkQueue):
            async def fetch_queued_items(self) -> list[WorkItem]:
                return []

        with pytest.raises(TypeError):
            IncompleteQueue()  # type: ignore[abstract]

    def test_complete_subclass_is_instantiable(self) -> None:
        """Subclass implementing all abstract methods is instantiable."""

        class CompleteQueue(IWorkQueue):
            async def fetch_queued_items(self) -> list[WorkItem]:
                return []

            async def update_item_status(self, item: WorkItem, new_status: WorkItemStatus) -> bool:
                return True

        # Should not raise
        queue = CompleteQueue()
        assert isinstance(queue, IWorkQueue)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_import_from_queue_init(self) -> None:
        """IWorkQueue should be importable from queue/__init__.py."""
        from src.queue import IWorkQueue  # noqa: F401

        # If import succeeds, test passes
        assert True

    def test_import_from_interfaces_module(self) -> None:
        """IWorkQueue should be importable from interfaces.py directly."""
        from src.queue.interfaces import IWorkQueue as ImportedQueue

        assert ImportedQueue is IWorkQueue
