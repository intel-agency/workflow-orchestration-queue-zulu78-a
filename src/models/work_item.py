"""OS-APOW Unified Work Item Model.

Canonical data model shared by both the Sentinel Orchestrator and the
Work Event Notifier. Both components import from this module to prevent
model divergence.

See: OS-APOW Plan Review, I-1 / R-3
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(StrEnum):
    """The kind of work the agent should perform.

    Values:
        PLAN: Planning task (architecture, design, analysis)
        IMPLEMENT: Implementation task (coding, building)
        BUGFIX: Bug fix task (defect remediation)
    """

    PLAN = "PLAN"
    IMPLEMENT = "IMPLEMENT"
    BUGFIX = "BUGFIX"


class WorkItemStatus(StrEnum):
    """Maps directly to GitHub Issue labels used as state indicators.

    Values map to corresponding GitHub labels:
        QUEUED: agent:queued - Issue is queued for agent processing
        IN_PROGRESS: agent:in-progress - Agent is actively working
        RECONCILING: agent:reconciling - Agent is reconciling state
        SUCCESS: agent:success - Agent completed work successfully
        ERROR: agent:error - Agent encountered an error
        INFRA_FAILURE: agent:infra-failure - Infrastructure failure
        STALLED_BUDGET: agent:stalled-budget - Agent stalled due to budget
    """

    QUEUED = "agent:queued"
    IN_PROGRESS = "agent:in-progress"
    RECONCILING = "agent:reconciling"
    SUCCESS = "agent:success"
    ERROR = "agent:error"
    INFRA_FAILURE = "agent:infra-failure"
    STALLED_BUDGET = "agent:stalled-budget"


class WorkItem(BaseModel):
    """Unified work item used across all OS-APOW components.

    This model represents a task from any provider (GitHub, Linear, etc.)
    in a provider-agnostic format. All provider-specific data goes into
    the metadata dict field to keep the core model portable.

    Attributes:
        id: Unique identifier for the work item (string or integer)
        source_url: URL to the original issue/task
        context_body: Body content of the issue/task
        target_repo_slug: Target repository in owner/repo format
        task_type: Classification of task type (PLAN, IMPLEMENT, BUGFIX)
        status: Current status of the work item
        metadata: Provider-specific info (e.g., issue_node_id, issue_number)

    Example:
        >>> item = WorkItem(
        ...     id="12345",
        ...     source_url="https://github.com/owner/repo/issues/42",
        ...     context_body="Implement the new feature",
        ...     target_repo_slug="owner/repo",
        ...     task_type=TaskType.IMPLEMENT,
        ...     status=WorkItemStatus.QUEUED,
        ...     metadata={"issue_number": 42, "node_id": "I_abc123"}
        ... )
    """

    id: str | int = Field(..., description="Unique identifier for the work item")
    source_url: str = Field(..., description="URL to the original issue/task")
    context_body: str = Field(default="", description="Body content of the issue/task")
    target_repo_slug: str = Field(..., description="Target repository in owner/repo format")
    task_type: TaskType = Field(..., description="Classification of task type")
    status: WorkItemStatus = Field(..., description="Current status of the work item")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific info (e.g., issue_node_id, issue_number)",
    )


# --- Credential Scrubber (R-7) ---
# Regex patterns that match common secret formats. Used to sanitize
# worker output before posting to GitHub issue comments.

# NOTE: These patterns use synthetic test-safe formats that won't trigger
# gitleaks. Real patterns would use actual provider prefixes.

_SECRET_PATTERNS = [
    # GitHub PAT (classic) - ghp_ prefix
    re.compile(r"ghp_[A-Za-z0-9_]{36,}"),
    # GitHub App installation token - ghs_ prefix
    re.compile(r"ghs_[A-Za-z0-9_]{36,}"),
    # GitHub OAuth token - gho_ prefix
    re.compile(r"gho_[A-Za-z0-9_]{36,}"),
    # GitHub fine-grained PAT
    re.compile(r"github_pat_[A-Za-z0-9_]{22,}"),
    # Bearer tokens
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    # Generic token patterns
    re.compile(r"token\s+[A-Za-z0-9\-._~+/]{20,}", re.IGNORECASE),
    # OpenAI-style API keys
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    # ZhipuAI keys
    re.compile(r"[A-Za-z0-9]{32,}\.zhipu[A-Za-z0-9]*"),
]


def scrub_secrets(text: str, replacement: str = "***REDACTED***") -> str:
    """Strip known secret patterns from text for safe public posting.

    This function removes credential patterns from text before posting
    to GitHub issue comments or other public locations.

    Args:
        text: The input text to sanitize
        replacement: The string to replace secrets with (default: "***REDACTED***")

    Returns:
        The sanitized text with all matching secret patterns replaced

    Example:
        >>> scrub_secrets("Token: ghp_abc123...")
        'Token: ***REDACTED***'
    """
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text
