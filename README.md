# OS-APOW

> **Headless Agentic Orchestration Platform** — Transforms GitHub Issues into automated execution orders for specialized AI agents.

> **AI Agent Quick Reference:** See [`.ai-repository-summary.md`](./.ai-repository-summary.md) for a structured overview designed for AI agents.

## Overview

OS-APOW (Open Source - Agentic Process Orchestration Workflow) is a Python-based platform that bridges GitHub Issues with AI agent execution. It consists of two primary services:

- **Notifier Service** — FastAPI webhook receiver that maps GitHub events to a unified work item queue
- **Sentinel Orchestrator** — Background worker that polls for queued tasks, claims them via distributed locking, and manages the AI agent lifecycle

## Tech Stack

| Category | Technology |
|----------|-----------|
| Language | Python 3.12+ |
| Package Manager | uv |
| Web Framework | FastAPI + Uvicorn |
| HTTP Client | HTTPX |
| Data Validation | Pydantic |
| Testing | pytest, pytest-asyncio, pytest-cov |
| Linting/Formatting | ruff, mypy |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (optional, for containerized runs)

### Install

```bash
# Clone the repo
git clone https://github.com/intel-agency/workflow-orchestration-queue-zulu78-a.git
cd workflow-orchestration-queue-zulu78-a

# Install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate
```

### Run

```bash
# Start the notifier (webhook receiver)
uv run uvicorn src.notifier_service:app --reload --port 8000

# Or start the sentinel orchestrator (requires env vars)
uv run python -m src.orchestrator_sentinel
```

### Docker

```bash
# Build and run all services
docker compose up --build

# Run just the notifier
docker compose up notifier
```

## Development

### Install dev dependencies

```bash
uv sync --extra dev
```

### Run tests

```bash
uv run pytest
uv run pytest --cov=src --cov-report=term-missing
```

### Lint and format

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```

### Run all validation

```bash
pwsh -NoProfile -File ./scripts/validate.ps1 -All
```

## Project Structure

```
.
├── src/                          # Application source
│   ├── __init__.py
│   ├── notifier_service.py       # FastAPI webhook receiver
│   ├── orchestrator_sentinel.py  # Sentinel orchestrator
│   ├── models/
│   │   ├── __init__.py
│   │   └── work_item.py          # Unified work item model + credential scrubber
│   └── queue/
│       ├── __init__.py
│       └── github_queue.py       # GitHub-backed task queue
├── tests/                        # Python test suite (pytest)
│   ├── models/
│   ├── queue/
│   └── test_services.py
├── test/                         # Shell/Pester devcontainer tests
├── scripts/                      # Utility scripts (PowerShell, Bash)
├── docs/                         # Project documentation
├── plan_docs/                    # External planning documents
├── .github/                      # GitHub Actions workflows & config
├── .devcontainer/                # Consumer devcontainer config
├── pyproject.toml                # Python project config
├── Dockerfile                    # Multi-stage app build
├── docker-compose.yml            # Service orchestration
└── AGENTS.md                     # Agent instructions
```

## Architecture

The system uses GitHub Issues as a queue backend ("Markdown as Database"):

1. **Notifier** receives webhook events → creates `WorkItem` → labels issue `agent:queued`
2. **Sentinel** polls for `agent:queued` issues → claims via assign-then-verify → spawns AI agent in devcontainer → reports results

State transitions: `agent:queued` → `agent:in-progress` → `agent:success` / `agent:error`

See [docs/architecture.md](docs/architecture.md) for detailed architecture diagrams.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub authentication token |
| `GITHUB_ORG` | Sentinel | GitHub organization name |
| `GITHUB_REPO` | Sentinel | GitHub repository name |
| `WEBHOOK_SECRET` | Notifier | HMAC secret for webhook validation |
| `SENTINEL_BOT_LOGIN` | No | Bot account login for distributed locking |

## License

MIT
