"""Unit tests for WorkItem model, TaskType, WorkItemStatus, and scrub_secrets.

These tests validate the core models used across all OS-APOW components.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.work_item import (
    TaskType,
    WorkItem,
    WorkItemStatus,
    scrub_secrets,
)


class TestTaskType:
    """Tests for TaskType enum."""

    def test_task_type_plan_value(self) -> None:
        """TaskType.PLAN should have value 'PLAN'."""
        assert TaskType.PLAN.value == "PLAN"

    def test_task_type_implement_value(self) -> None:
        """TaskType.IMPLEMENT should have value 'IMPLEMENT'."""
        assert TaskType.IMPLEMENT.value == "IMPLEMENT"

    def test_task_type_bugfix_value(self) -> None:
        """TaskType.BUGFIX should have value 'BUGFIX'."""
        assert TaskType.BUGFIX.value == "BUGFIX"

    def test_task_type_count(self) -> None:
        """TaskType should have exactly 3 values."""
        assert len(TaskType) == 3

    def test_task_type_string_conversion(self) -> None:
        """TaskType should convert to string properly."""
        assert str(TaskType.PLAN) == "PLAN"
        assert TaskType.PLAN.value == "PLAN"


class TestWorkItemStatus:
    """Tests for WorkItemStatus enum."""

    def test_queued_value(self) -> None:
        """WorkItemStatus.QUEUED should map to 'agent:queued'."""
        assert WorkItemStatus.QUEUED.value == "agent:queued"

    def test_in_progress_value(self) -> None:
        """WorkItemStatus.IN_PROGRESS should map to 'agent:in-progress'."""
        assert WorkItemStatus.IN_PROGRESS.value == "agent:in-progress"

    def test_reconciling_value(self) -> None:
        """WorkItemStatus.RECONCILING should map to 'agent:reconciling'."""
        assert WorkItemStatus.RECONCILING.value == "agent:reconciling"

    def test_success_value(self) -> None:
        """WorkItemStatus.SUCCESS should map to 'agent:success'."""
        assert WorkItemStatus.SUCCESS.value == "agent:success"

    def test_error_value(self) -> None:
        """WorkItemStatus.ERROR should map to 'agent:error'."""
        assert WorkItemStatus.ERROR.value == "agent:error"

    def test_infra_failure_value(self) -> None:
        """WorkItemStatus.INFRA_FAILURE should map to 'agent:infra-failure'."""
        assert WorkItemStatus.INFRA_FAILURE.value == "agent:infra-failure"

    def test_stalled_budget_value(self) -> None:
        """WorkItemStatus.STALLED_BUDGET should map to 'agent:stalled-budget'."""
        assert WorkItemStatus.STALLED_BUDGET.value == "agent:stalled-budget"

    def test_status_count(self) -> None:
        """WorkItemStatus should have exactly 7 values."""
        assert len(WorkItemStatus) == 7

    def test_all_statuses_have_agent_prefix(self) -> None:
        """All WorkItemStatus values should start with 'agent:'."""
        for status in WorkItemStatus:
            assert status.value.startswith("agent:"), f"{status} should have 'agent:' prefix"


class TestWorkItem:
    """Tests for WorkItem Pydantic model."""

    @pytest.fixture
    def valid_work_item_data(self) -> dict:
        """Fixture providing valid work item data."""
        return {
            "id": "12345",
            "source_url": "https://github.com/owner/repo/issues/42",
            "context_body": "Implement the new feature",
            "target_repo_slug": "owner/repo",
            "task_type": TaskType.IMPLEMENT,
            "status": WorkItemStatus.QUEUED,
            "metadata": {"issue_number": 42, "node_id": "I_abc123"},
        }

    def test_create_work_item_with_all_fields(self, valid_work_item_data: dict) -> None:
        """WorkItem should be created successfully with all fields."""
        item = WorkItem(**valid_work_item_data)
        assert item.id == "12345"
        assert item.source_url == "https://github.com/owner/repo/issues/42"
        assert item.context_body == "Implement the new feature"
        assert item.target_repo_slug == "owner/repo"
        assert item.task_type == TaskType.IMPLEMENT
        assert item.status == WorkItemStatus.QUEUED
        assert item.metadata == {"issue_number": 42, "node_id": "I_abc123"}

    def test_create_work_item_with_minimal_fields(self) -> None:
        """WorkItem should be created with only required fields."""
        item = WorkItem(
            id="1",
            source_url="https://github.com/owner/repo/issues/1",
            target_repo_slug="owner/repo",
            task_type=TaskType.PLAN,
            status=WorkItemStatus.QUEUED,
        )
        assert item.id == "1"
        assert item.context_body == ""
        assert item.metadata == {}

    def test_work_item_with_integer_id(self) -> None:
        """WorkItem should accept integer id."""
        item = WorkItem(
            id=12345,
            source_url="https://github.com/owner/repo/issues/42",
            target_repo_slug="owner/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.IN_PROGRESS,
        )
        assert item.id == 12345
        assert isinstance(item.id, int)

    def test_work_item_default_context_body(self, valid_work_item_data: dict) -> None:
        """WorkItem should default context_body to empty string."""
        del valid_work_item_data["context_body"]
        item = WorkItem(**valid_work_item_data)
        assert item.context_body == ""

    def test_work_item_default_metadata(self, valid_work_item_data: dict) -> None:
        """WorkItem should default metadata to empty dict."""
        del valid_work_item_data["metadata"]
        item = WorkItem(**valid_work_item_data)
        assert item.metadata == {}

    def test_work_item_missing_id_raises_validation_error(self, valid_work_item_data: dict) -> None:
        """WorkItem should raise ValidationError when id is missing."""
        del valid_work_item_data["id"]
        with pytest.raises(ValidationError) as exc_info:
            WorkItem(**valid_work_item_data)
        assert "id" in str(exc_info.value)

    def test_work_item_missing_source_url_raises_validation_error(
        self, valid_work_item_data: dict
    ) -> None:
        """WorkItem should raise ValidationError when source_url is missing."""
        del valid_work_item_data["source_url"]
        with pytest.raises(ValidationError) as exc_info:
            WorkItem(**valid_work_item_data)
        assert "source_url" in str(exc_info.value)

    def test_work_item_missing_target_repo_slug_raises_validation_error(
        self, valid_work_item_data: dict
    ) -> None:
        """WorkItem should raise ValidationError when target_repo_slug is missing."""
        del valid_work_item_data["target_repo_slug"]
        with pytest.raises(ValidationError) as exc_info:
            WorkItem(**valid_work_item_data)
        assert "target_repo_slug" in str(exc_info.value)

    def test_work_item_missing_task_type_raises_validation_error(
        self, valid_work_item_data: dict
    ) -> None:
        """WorkItem should raise ValidationError when task_type is missing."""
        del valid_work_item_data["task_type"]
        with pytest.raises(ValidationError) as exc_info:
            WorkItem(**valid_work_item_data)
        assert "task_type" in str(exc_info.value)

    def test_work_item_missing_status_raises_validation_error(
        self, valid_work_item_data: dict
    ) -> None:
        """WorkItem should raise ValidationError when status is missing."""
        del valid_work_item_data["status"]
        with pytest.raises(ValidationError) as exc_info:
            WorkItem(**valid_work_item_data)
        assert "status" in str(exc_info.value)

    def test_work_item_invalid_task_type_raises_validation_error(
        self, valid_work_item_data: dict
    ) -> None:
        """WorkItem should raise ValidationError for invalid task_type."""
        valid_work_item_data["task_type"] = "INVALID"
        with pytest.raises(ValidationError):
            WorkItem(**valid_work_item_data)

    def test_work_item_invalid_status_raises_validation_error(
        self, valid_work_item_data: dict
    ) -> None:
        """WorkItem should raise ValidationError for invalid status."""
        valid_work_item_data["status"] = "invalid-status"
        with pytest.raises(ValidationError):
            WorkItem(**valid_work_item_data)

    def test_work_item_model_dump(self, valid_work_item_data: dict) -> None:
        """WorkItem should serialize correctly via model_dump()."""
        item = WorkItem(**valid_work_item_data)
        data = item.model_dump()
        assert data["id"] == "12345"
        assert data["task_type"] == TaskType.IMPLEMENT
        assert data["status"] == WorkItemStatus.QUEUED

    def test_work_item_json_serialization(self, valid_work_item_data: dict) -> None:
        """WorkItem should serialize to JSON correctly."""
        item = WorkItem(**valid_work_item_data)
        json_str = item.model_dump_json()
        assert '"id":"12345"' in json_str
        assert '"task_type":"IMPLEMENT"' in json_str
        assert '"status":"agent:queued"' in json_str


class TestScrubSecrets:
    """Tests for scrub_secrets utility function."""

    def test_scrub_github_pat_classic(self) -> None:
        """scrub_secrets should redact GitHub PAT (classic) format."""
        # Using synthetic test-safe format (not real ghp_ pattern)
        text = "Token: ghp_abcdefghijklmnopqrstuvwxyz0123456789"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "***REDACTED***" in result

    def test_scrub_github_app_token(self) -> None:
        """scrub_secrets should redact GitHub App installation token format."""
        text = "App token: ghs_abcdefghijklmnopqrstuvwxyz0123456789"
        result = scrub_secrets(text)
        assert "ghs_" not in result
        assert "***REDACTED***" in result

    def test_scrub_github_oauth_token(self) -> None:
        """scrub_secrets should redact GitHub OAuth token format."""
        text = "OAuth: gho_abcdefghijklmnopqrstuvwxyz0123456789"
        result = scrub_secrets(text)
        assert "gho_" not in result
        assert "***REDACTED***" in result

    def test_scrub_github_fine_grained_pat(self) -> None:
        """scrub_secrets should redact GitHub fine-grained PAT format."""
        text = "Fine-grained: github_pat_abcdefghijklmnopqrstuvwxyz"
        result = scrub_secrets(text)
        assert "github_pat_" not in result
        assert "***REDACTED***" in result

    def test_scrub_bearer_token(self) -> None:
        """scrub_secrets should redact Bearer tokens."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9=="
        result = scrub_secrets(text)
        assert "Bearer eyJ" not in result

    def test_scrub_generic_token(self) -> None:
        """scrub_secrets should redact generic token patterns."""
        text = "token abcdefghijklmnopqrstuvwxyz123456"
        result = scrub_secrets(text)
        assert "token abcdef" not in result

    def test_scrub_openai_key(self) -> None:
        """scrub_secrets should redact OpenAI-style API keys."""
        text = "API Key: sk-abcdefghijklmnopqrstuvwxyz123456"
        result = scrub_secrets(text)
        assert "sk-abc" not in result
        assert "***REDACTED***" in result

    def test_scrub_zhipuai_key(self) -> None:
        """scrub_secrets should redact ZhipuAI keys."""
        text = "ZhipuAI: abcdefghijklmnopqrstuvwxyz12345678.zhipuXYZ"
        result = scrub_secrets(text)
        assert "zhipu" not in result or "***REDACTED***" in result

    def test_scrub_no_secrets(self) -> None:
        """scrub_secrets should return unchanged text if no secrets found."""
        text = "This is a normal message with no secrets."
        result = scrub_secrets(text)
        assert result == text

    def test_scrub_empty_string(self) -> None:
        """scrub_secrets should handle empty string."""
        result = scrub_secrets("")
        assert result == ""

    def test_scrub_multiple_secrets(self) -> None:
        """scrub_secrets should redact multiple secrets in one string."""
        text = "ghp_abcdefghijklmnopqrstuvwxyz0123456789 and sk-abcdefghijklmnopqrstuvwxyz123456"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "sk-abc" not in result
        assert result.count("***REDACTED***") >= 2

    def test_scrub_custom_replacement(self) -> None:
        """scrub_secrets should use custom replacement string."""
        text = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
        result = scrub_secrets(text, replacement="[HIDDEN]")
        assert "[HIDDEN]" in result
        assert "ghp_" not in result


class TestModuleImports:
    """Tests for module-level imports."""

    def test_import_from_models_init(self) -> None:
        """All public symbols should be importable from models/__init__.py."""
        from src.models import TaskType, WorkItem, WorkItemStatus, scrub_secrets  # noqa: F401

        # If import succeeds, test passes
        assert True

    def test_import_from_work_item_module(self) -> None:
        """All symbols should be importable from work_item.py directly."""
        from src.models.work_item import (
            TaskType,
            WorkItem,
            WorkItemStatus,
            scrub_secrets,
        )

        assert TaskType is not None
        assert WorkItem is not None
        assert WorkItemStatus is not None
        assert scrub_secrets is not None
