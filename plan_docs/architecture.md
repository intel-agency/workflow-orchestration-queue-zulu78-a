# System Architecture — OS-APOW (workflow-orchestration-queue)

> **Summary:** This document describes the high-level architecture for OS-APOW, a headless agentic orchestration platform that transforms GitHub Issues into automated execution orders for specialized AI agents.

---

## Architecture Overview

OS-APOW is built on **Four Pillars** — distinct subsystems that work together to enable autonomous software development:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OS-APOW System                                  │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   THE EAR       │   THE STATE     │   THE BRAIN     │   THE HANDS           │
│   (Notifier)    │   (Queue)       │   (Sentinel)    │   (Worker)            │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│ FastAPI         │ GitHub Issues   │ Python Async    │ DevContainer          │
│ Webhook         │ Labels          │ Polling         │ opencode CLI          │
│ Receiver        │ Milestones      │ Dispatcher      │ LLM Agent             │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

## The Four Pillars

### 1. The Ear (Work Event Notifier)

- **Technology:** FastAPI + Uvicorn + Pydantic
- **Responsibilities:**
  - Secure webhook ingestion at `/webhooks/github`
  - HMAC SHA256 signature verification against `WEBHOOK_SECRET`
  - Intelligent event triage and routing
  - WorkItem manifest generation from GitHub payloads
  - Queue initialization by applying `agent:queued` label

### 2. The State (Work Queue)

- **Philosophy:** "Markdown as a Database"
- **Implementation:** GitHub Issues + Labels + Milestones
- **State Machine:**

| Label | State | Description |
|-------|-------|-------------|
| `agent:queued` | QUEUED | Awaiting available Sentinel |
| `agent:in-progress` | IN_PROGRESS | Claimed by a Sentinel |
| `agent:reconciling` | RECONCILING | Stale task being recovered |
| `agent:success` | SUCCESS | Workflow completed successfully |
| `agent:error` | ERROR | Execution error occurred |
| `agent:infra-failure` | INFRA_FAILURE | Infrastructure failure |
| `agent:stalled-budget` | STALLED_BUDGET | Budget/token limit exceeded |

- **Concurrency Control:** Assign-then-verify pattern using GitHub Assignees as distributed locks

### 3. The Brain (Sentinel Orchestrator)

- **Technology:** Python 3.12+ Async + HTTPX + Shell Bridge
- **Responsibilities:**
  - Polling Discovery (every 60 seconds) for `agent:queued` issues
  - Task Claiming via assign-then-verify pattern
  - Environment Management: `up` → `start` → `prompt`
  - Heartbeat System (background async coroutine, 5-minute intervals)
  - Graceful Shutdown (SIGTERM/SIGINT handling)
  - Auth Synchronization (gh-auth.ps1, common-auth.ps1)

### 4. The Hands (Opencode Worker)

- **Technology:** DevContainer + opencode CLI + LLM
- **Responsibilities:**
  - Execute markdown instructions from workflow modules
  - Run local test suites for verification
  - Submit formatted Pull Requests
  - Maintain contextual awareness via vector indexing

## Data Flow (Happy Path)

```
1. User opens Issue with [Application Plan] title
              │
              ▼
2. GitHub Webhook → Notifier (FastAPI)
              │
              ▼
3. Notifier validates signature, adds agent:queued label
              │
              ▼
4. Sentinel polls, discovers queued issue
              │
              ▼
5. Sentinel claims via assign-then-verify
              │
              ▼
6. Sentinel: up → start → prompt (workflow)
              │
              ▼
7. Worker executes markdown instructions
              │
              ▼
8. Worker creates PR, posts completion comment
              │
              ▼
9. Sentinel labels issue agent:success
```

## Key Architectural Decisions

### ADR 07: Standardized Shell-Bridge Execution
The Sentinel communicates with Workers exclusively through `devcontainer-opencode.sh`, ensuring environment parity and preventing direct Docker SDK coupling.

### ADR 08: Polling-First Resiliency Model
Polling ensures self-healing on restart; webhooks are an optimization layer. If the server crashes, the Sentinel naturally re-syncs by scanning GitHub labels.

### ADR 09: Provider-Agnostic Interface Layer
The `ITaskQueue` interface decouples orchestrator logic from the specific provider (GitHub, Linear, Jira, etc.), preventing vendor lock-in.

## Project Structure

```
workflow-orchestration-queue/
├── pyproject.toml              # uv dependencies and metadata
├── uv.lock                     # Deterministic lockfile
├── src/
│   ├── os_apow/
│   │   ├── __init__.py
│   │   ├── main.py             # Entry points (run_notifier, run_sentinel)
│   │   ├── config.py           # Pydantic Settings configuration
│   │   ├── api/
│   │   │   ├── deps.py         # FastAPI dependency injection
│   │   │   └── routes/
│   │   │       └── webhooks.py # GitHub webhook endpoints
│   │   ├── models/
│   │   │   └── work_item.py    # WorkItem, TaskType, WorkItemStatus
│   │   ├── services/
│   │   │   ├── github_client.py # HTTPX-based GitHub API wrapper
│   │   │   ├── queue.py        # ITaskQueue + GitHubQueue implementation
│   │   │   └── worker.py       # SentinelWorker orchestrator
│   │   └── utils/
│   │       └── logging.py      # Structured JSON logging
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_api/
│   │   └── test_webhooks.py    # Webhook endpoint tests
│   ├── test_models/
│   │   └── test_work_item.py   # WorkItem model tests
│   └── test_services/
│       └── test_queue.py       # Queue implementation tests
├── scripts/
│   ├── devcontainer-opencode.sh # Shell bridge
│   ├── gh-auth.ps1             # GitHub auth helper
│   └── update-remote-indices.ps1 # Vector index sync
├── local_ai_instruction_modules/ # Markdown workflow prompts
│   ├── create-app-plan.md
│   ├── perform-task.md
│   └── recover-from-error.md
└── plan_docs/                  # Architecture and planning documentation
```

## Security Architecture

- **Network Isolation:** Worker containers in dedicated Docker networks
- **Credential Management:** Tokens injected as temp env vars, never written to disk
- **Resource Constraints:** 2 CPUs, 4GB RAM cap per worker
- **Credential Scrubbing:** Regex strips `ghp_*`, `ghs_*`, `sk-*`, Bearer tokens
- **Webhook Validation:** HMAC SHA256 prevents unauthorized payload injection

## References

- [Tech Stack](./tech-stack.md) — Full technology stack details
- [Architecture Guide v3.2](./OS-APOW%20Architecture%20Guide%20v3.2.md) — Detailed architecture with ADRs
- [Development Plan v4.2](./OS-APOW%20Development%20Plan%20v4.2.md) — Phased roadmap and user stories
- [Implementation Specification v1.2](./OS-APOW%20Implementation%20Specification%20v1.2.md) — Detailed requirements and test cases
