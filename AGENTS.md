# AGENTS.md

> Instructions for AI coding agents working on OS-APOW

## Project Overview

OS-APOW (workflow-orchestration-queue) is a **headless agentic orchestration platform** that transforms GitHub Issues into automated execution orders for specialized AI agents. The system moves AI from a passive co-pilot role to an autonomous background production service.

### Four Pillars Architecture

| Component | Name | Technology | Purpose |
|-----------|------|------------|---------|
| The Ear | Notifier | FastAPI + Uvicorn | Webhook receiver with HMAC validation |
| The State | Queue | GitHub Issues + Labels | State machine using labels |
| The Brain | Sentinel | Python Async + HTTPX | Polling and task dispatch |
| The Hands | Worker | DevContainer + opencode CLI | LLM agent execution |

## Setup Commands

```bash
# Install dependencies (including dev dependencies)
uv sync --extra dev

# Run the notifier service (webhook receiver)
uv run os-apow-notifier

# Run the sentinel service (background polling)
uv run os-apow-sentinel

# Run with Docker
docker-compose up -d
```

## Project Structure

```
src/os_apow/
├── __init__.py              # Package initialization
├── main.py                  # Entry points (run_notifier, run_sentinel)
├── config.py                # Pydantic Settings configuration
├── api/
│   ├── __init__.py
│   ├── deps.py              # FastAPI dependency injection
│   └── routes/
│       ├── __init__.py
│       └── webhooks.py      # GitHub webhook endpoints (/webhooks/github, /health)
├── models/
│   ├── __init__.py
│   └── work_item.py         # WorkItem, TaskType, WorkItemStatus, scrub_secrets()
├── services/
│   ├── __init__.py
│   ├── github_client.py     # HTTPX-based GitHub API wrapper
│   ├── queue.py             # ITaskQueue interface + GitHubQueue implementation
│   └── worker.py            # SentinelWorker orchestrator
└── utils/
    ├── __init__.py
    └── logging.py           # Structured JSON logging setup

tests/
├── conftest.py              # Pytest fixtures (mock_settings, sample_work_item)
├── test_api/
│   └── test_webhooks.py     # Webhook signature validation, endpoint tests
├── test_models/
│   └── test_work_item.py    # WorkItem model tests, scrub_secrets tests
└── test_services/
    └── test_queue.py        # Queue implementation tests
```

## Code Style

### Linting and Formatting

```bash
# Check linting
uv run ruff check src tests

# Auto-fix linting issues
uv run ruff check --fix src tests

# Check formatting
uv run ruff format --check src tests

# Apply formatting
uv run ruff format src tests
```

### Type Checking

```bash
# Run mypy with strict mode
uv run mypy src
```

### Conventions

- **Line length:** 100 characters (configured in pyproject.toml)
- **Python version:** 3.12+
- **Imports:** Use `isort` via ruff; first-party imports from `os_apow`
- **Type hints:** Required on all functions (mypy strict mode)
- **Async patterns:** Use `asyncio` and `httpx.AsyncClient` throughout
- **Docstrings:** Use triple-quoted docstrings for modules, classes, and public functions

## Testing

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=os_apow --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_api/test_webhooks.py

# Run specific test class
uv run pytest tests/test_api/test_webhooks.py::TestWebhookSignature

# Run with verbose output
uv run pytest -v

# Collect tests without running
uv run pytest --collect-only
```

### Test Patterns

```python
# Use fixtures from conftest.py
def test_example(mock_settings: Settings, sample_work_item: WorkItem) -> None:
    assert mock_settings.github_org == "test-org"
    assert sample_work_item.issue_number == 42

# Async tests work automatically (pytest-asyncio with auto mode)
async def test_async_example(mock_async_client: AsyncMock) -> None:
    response = await mock_async_client.get("/test")
    assert response.status_code == 200

# Mock settings use fake keys for testing
# Use "FAKE-KEY-FOR-TESTING-*" pattern to avoid triggering secret scanners
```

## Configuration

All configuration uses environment variables with the `OS_APOW_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `OS_APOW_GITHUB_TOKEN` | GitHub authentication token | **Required** |
| `OS_APOW_GITHUB_ORG` | Organization name | Required |
| `OS_APOW_GITHUB_REPO` | Target repository (owner/repo) | Required |
| `OS_APOW_WEBHOOK_SECRET` | HMAC secret for webhooks | Required |
| `OS_APOW_WEBHOOK_PORT` | Webhook receiver port | 8000 |
| `OS_APOW_SENTINEL_ID` | Unique sentinel identifier | sentinel-001 |
| `OS_APOW_POLL_INTERVAL_SECONDS` | Polling interval | 60 |
| `OS_APOW_LOG_LEVEL` | Logging level | INFO |
| `OS_APOW_LOG_FORMAT` | Log format (json/text) | json |

Copy `.env.example` to `.env` and fill in values.

## State Machine Labels

GitHub Issue labels represent task state:

| Label | State | Description |
|-------|-------|-------------|
| `agent:queued` | QUEUED | Awaiting available Sentinel |
| `agent:in-progress` | IN_PROGRESS | Claimed by a Sentinel |
| `agent:reconciling` | RECONCILING | Stale task being recovered |
| `agent:success` | SUCCESS | Workflow completed successfully |
| `agent:error` | ERROR | Execution error occurred |
| `agent:infra-failure` | INFRA_FAILURE | Infrastructure failure |
| `agent:stalled-budget` | STALLED_BUDGET | Budget/token limit exceeded |

## Architecture Notes

### Security

- **HMAC Validation:** All webhooks validated against `X-Hub-Signature-256` header
- **Credential Scrubbing:** Use `scrub_secrets()` from `os_apow.models.work_item` before posting to GitHub
- **Secret Patterns:** The scrubber handles `ghp_*`, `ghs_*`, `gho_*`, `github_pat_*`, `Bearer`, `sk-*`, ZhipuAI keys

### Concurrency Control

- GitHub Assignees act as distributed locks
- Assign-then-verify pattern prevents race conditions
- Multiple Sentinel instances can safely coexist

### Data Model

```python
# Unified WorkItem used across all components
class WorkItem(BaseModel):
    id: str                    # GitHub issue ID
    issue_number: int          # Issue number
    source_url: str            # Issue URL
    context_body: str          # Issue body
    target_repo_slug: str      # owner/repo
    task_type: TaskType        # PLAN, IMPLEMENT, BUGFIX
    status: WorkItemStatus     # State machine label
    node_id: str               # GraphQL node ID
```

## PR and Commit Guidelines

### Before Committing

1. Run linting: `uv run ruff check src tests`
2. Run formatting: `uv run ruff format src tests`
3. Run type check: `uv run mypy src`
4. Run tests: `uv run pytest`
5. Verify all checks pass

### PR Requirements

- All CI checks must pass (lint, typecheck, test)
- New code requires tests
- Update documentation for public API changes
- Use conventional commit messages

### CI Pipeline

The CI pipeline runs on push to main and pull requests:

1. **lint:** ruff check and format verification
2. **typecheck:** mypy strict mode
3. **test:** pytest with coverage
4. **docker-build:** Docker image build (after lint + test pass)

## Common Pitfalls

### Credential Safety

Never commit real tokens. In tests, use the pattern:
```python
github_token="FAKE-KEY-FOR-TESTING-00000000"
```

Avoid prefixes that match real provider formats (`ghp_`, `ghs_`, `sk-`, etc.).

### Async Patterns

Use `httpx.AsyncClient` for HTTP requests:
```python
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### Pydantic Settings

Settings are cached via `@lru_cache`. Clear cache in tests if needed:
```python
from os_apow.config import get_settings
get_settings.cache_clear()
```

### Webhook Testing

Always include valid HMAC signature in webhook tests:
```python
import hmac
import hashlib

signature = "sha256=" + hmac.new(
    secret.encode(), payload, hashlib.sha256
).hexdigest()
```

## Related Documentation

- [README.md](README.md) - Project overview and quick start
- [.ai-repository-summary.md](.ai-repository-summary.md) - AI-friendly repository context
- [plan_docs/architecture.md](plan_docs/architecture.md) - Detailed architecture
- [plan_docs/tech-stack.md](plan_docs/tech-stack.md) - Technology decisions
