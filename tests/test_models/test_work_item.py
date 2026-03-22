"""
Tests for OS-APOW Models
"""

import pytest
from pydantic import ValidationError

from os_apow.models.work_item import TaskType, WorkItem, WorkItemStatus


class TestTaskType:
    """Tests for TaskType enum."""

    def test_task_type_values(self) -> None:
        """Test that TaskType has expected values."""
        assert TaskType.PLAN.value == "PLAN"
        assert TaskType.IMPLEMENT.value == "IMPLEMENT"
        assert TaskType.BUGFIX.value == "BUGFIX"


class TestWorkItemStatus:
    """Tests for WorkItemStatus enum."""

    def test_status_values(self) -> None:
        """Test that WorkItemStatus has expected label values."""
        assert WorkItemStatus.QUEUED.value == "agent:queued"
        assert WorkItemStatus.IN_PROGRESS.value == "agent:in-progress"
        assert WorkItemStatus.SUCCESS.value == "agent:success"
        assert WorkItemStatus.ERROR.value == "agent:error"
        assert WorkItemStatus.INFRA_FAILURE.value == "agent:infra-failure"


class TestWorkItem:
    """Tests for WorkItem model."""

    def test_create_work_item(self) -> None:
        """Test creating a valid WorkItem."""
        item = WorkItem(
            id="12345",
            issue_number=42,
            source_url="https://github.com/org/repo/issues/42",
            context_body="Test body",
            target_repo_slug="org/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            node_id="I_test123",
        )

        assert item.id == "12345"
        assert item.issue_number == 42
        assert item.task_type == TaskType.IMPLEMENT
        assert item.status == WorkItemStatus.QUEUED

    def test_work_item_defaults(self) -> None:
        """Test WorkItem default values."""
        item = WorkItem(
            id="12345",
            issue_number=42,
            source_url="https://github.com/org/repo/issues/42",
            target_repo_slug="org/repo",
            node_id="I_test123",
        )

        assert item.task_type == TaskType.IMPLEMENT
        assert item.status == WorkItemStatus.QUEUED
        assert item.context_body == ""

    def test_work_item_requires_required_fields(self) -> None:
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            WorkItem()  # type: ignore

    def test_work_item_from_dict(self) -> None:
        """Test creating WorkItem from dictionary."""
        data = {
            "id": "12345",
            "issue_number": 42,
            "source_url": "https://github.com/org/repo/issues/42",
            "context_body": "Test body",
            "target_repo_slug": "org/repo",
            "task_type": "PLAN",
            "status": "agent:queued",
            "node_id": "I_test123",
        }

        item = WorkItem(**data)
        assert item.task_type == TaskType.PLAN
        assert item.status == WorkItemStatus.QUEUED
