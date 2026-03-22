"""OS-APOW Work Queue Interfaces.

Abstract base class defining the standard interface for work queue operations.
This allows the orchestrator logic to be decoupled from specific providers
(GitHub, Linear, Jira, etc.).

See: OS-APOW Plan Review, I-1 / R-3
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.work_item import WorkItem, WorkItemStatus


class IWorkQueue(ABC):
    """Abstract interface for work queue operations.

    This abstract base class defines the standard interface that all work queue
    providers must implement. It allows the orchestrator to be provider-agnostic,
    enabling easy switching between GitHub Issues, Linear, Jira, or custom
    implementations.

    Subclasses must implement:
        - fetch_queued_items(): Retrieve items ready for processing
        - update_item_status(): Update the status of a work item

    Example:
        >>> class GitHubIssueQueue(IWorkQueue):
        ...     async def fetch_queued_items(self) -> list[WorkItem]:
        ...         # Implementation for GitHub Issues
        ...         pass
        ...     async def update_item_status(
        ...         self, item: WorkItem, new_status: WorkItemStatus
        ...     ) -> bool:
        ...         # Implementation for GitHub Issues
        ...         pass
    """

    @abstractmethod
    async def fetch_queued_items(self) -> list[WorkItem]:
        """Fetch all work items that are queued for processing.

        This method should retrieve all items from the queue that are in a
        "queued" state and ready to be picked up by workers.

        Returns:
            A list of WorkItem objects representing queued tasks.

        Raises:
            ProviderError: If the provider API returns an error.
            RateLimitError: If the provider rate limit is exceeded.

        Example:
            >>> queue = MyWorkQueue()
            >>> items = await queue.fetch_queued_items()
            >>> for item in items:
            ...     print(f"Processing {item.id}: {item.context_body[:50]}")
        """
        ...

    @abstractmethod
    async def update_item_status(self, item: WorkItem, new_status: WorkItemStatus) -> bool:
        """Update the status of a work item in the queue.

        This method should update the status of the work item in the underlying
        provider (e.g., update GitHub labels). It should return True if the
        update was successful, False otherwise.

        Args:
            item: The WorkItem to update.
            new_status: The new status to set for the item.

        Returns:
            True if the status was successfully updated, False otherwise.

        Raises:
            ProviderError: If the provider API returns an error.
            RateLimitError: If the provider rate limit is exceeded.

        Example:
            >>> success = await queue.update_item_status(item, WorkItemStatus.IN_PROGRESS)
            >>> if success:
            ...     print(f"Started processing {item.id}")
        """
        ...

    async def close(self) -> None:
        """Release resources and cleanup connections.

        This method should be called during graceful shutdown to release
        any resources held by the queue implementation (e.g., HTTP connections,
        database connections).

        Subclasses can override this method if they need to perform cleanup.
        The default implementation does nothing.

        Example:
            >>> async with lifespan(app):
            ...     queue = MyWorkQueue()
            ...     try:
            ...         items = await queue.fetch_queued_items()
            ...     finally:
            ...         await queue.close()
        """
        ...  # pragma: no cover
