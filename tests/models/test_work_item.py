"""Tests for the WorkItem model and credential scrubber."""

import pydantic
import pytest

from src.models.work_item import TaskType, WorkItem, WorkItemStatus, scrub_secrets


class TestTaskType:
    """Tests for the TaskType enum."""

    def test_plan_value(self):
        assert TaskType.PLAN.value == "PLAN"

    def test_implement_value(self):
        assert TaskType.IMPLEMENT.value == "IMPLEMENT"

    def test_bugfix_value(self):
        assert TaskType.BUGFIX.value == "BUGFIX"

    def test_all_members(self):
        assert set(TaskType.__members__.keys()) == {"PLAN", "IMPLEMENT", "BUGFIX"}


class TestWorkItemStatus:
    """Tests for the WorkItemStatus enum."""

    def test_queued_value(self):
        assert WorkItemStatus.QUEUED.value == "agent:queued"

    def test_in_progress_value(self):
        assert WorkItemStatus.IN_PROGRESS.value == "agent:in-progress"

    def test_success_value(self):
        assert WorkItemStatus.SUCCESS.value == "agent:success"

    def test_error_value(self):
        assert WorkItemStatus.ERROR.value == "agent:error"

    def test_all_members(self):
        expected = {
            "QUEUED",
            "IN_PROGRESS",
            "RECONCILING",
            "SUCCESS",
            "ERROR",
            "INFRA_FAILURE",
            "STALLED_BUDGET",
        }
        assert set(WorkItemStatus.__members__.keys()) == expected


class TestWorkItem:
    """Tests for the WorkItem Pydantic model."""

    def _make_work_item(self, **overrides):
        defaults = {
            "id": "test-123",
            "issue_number": 42,
            "source_url": "https://github.com/org/repo/issues/42",
            "context_body": "Test body",
            "target_repo_slug": "org/repo",
            "task_type": TaskType.IMPLEMENT,
            "status": WorkItemStatus.QUEUED,
            "node_id": "node_abc",
        }
        defaults.update(overrides)
        return WorkItem(**defaults)

    def test_create_work_item(self):
        item = self._make_work_item()
        assert item.id == "test-123"
        assert item.issue_number == 42
        assert item.task_type == TaskType.IMPLEMENT
        assert item.status == WorkItemStatus.QUEUED

    def test_work_item_serialization(self):
        item = self._make_work_item()
        data = item.model_dump()
        assert data["id"] == "test-123"
        assert data["task_type"] == TaskType.IMPLEMENT

    def test_work_item_from_dict(self):
        data = {
            "id": "test-456",
            "issue_number": 10,
            "source_url": "https://github.com/org/repo/issues/10",
            "context_body": "Plan task",
            "target_repo_slug": "org/repo",
            "task_type": TaskType.PLAN,
            "status": WorkItemStatus.QUEUED,
            "node_id": "node_def",
        }
        item = WorkItem(**data)
        assert item.task_type == TaskType.PLAN

    def test_missing_required_field(self):
        with pytest.raises(pydantic.ValidationError):
            WorkItem(id="test")


class TestScrubSecrets:
    """Tests for the credential scrubber."""

    def test_scrub_github_pat(self):
        # ghp_ followed by 36+ alphanumeric chars
        text = "token is ghp_ABCDEFGHabcdefgh0123456789ABCDEFGHabcdefgh"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "***REDACTED***" in result

    def test_scrub_github_app_token(self):
        # ghs_ followed by 36+ alphanumeric chars
        text = "token is ghs_ABCDEFGHabcdefgh0123456789ABCDEFGHabcdefgh"
        result = scrub_secrets(text)
        assert "ghs_" not in result

    def test_scrub_bearer_token(self):
        text = "Authorization: Bearer abc123def456ghi789jkl012mno345pqr678stu=="
        result = scrub_secrets(text)
        assert "Bearer" not in result or "***REDACTED***" in result

    def test_scrub_openai_key(self):
        # sk- followed by 20+ alphanumeric chars (no hyphens in the key part)
        text = "key: sk-abcdefghijklmnopqrstuvwxyz0123456789"
        result = scrub_secrets(text)
        assert "sk-abcdef" not in result

    def test_clean_text_passes_through(self):
        text = "This is clean text with no secrets."
        assert scrub_secrets(text) == text

    def test_custom_replacement(self):
        text = "ghp_ABCDEFGHabcdefgh0123456789ABCDEFGHabcdefgh"
        result = scrub_secrets(text, replacement="[HIDDEN]")
        assert "[HIDDEN]" in result

    def test_scrub_multiple_secrets(self):
        text = (
            "pat: ghp_ABCDEFGHabcdefgh0123456789ABCDEFGHabcdefgh and "
            "key: sk-abcdefghijklmnopqrstuvwxyz0123456789"
        )
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "sk-abcdef" not in result
        assert result.count("***REDACTED***") >= 2
