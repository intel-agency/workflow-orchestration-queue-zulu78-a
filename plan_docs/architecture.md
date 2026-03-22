# OS-APOW Architecture

## Executive Summary

OS-APOW (workflow-orchestration-queue) is a headless agentic orchestration platform that transforms standard project management artifacts (GitHub Issues) into automated execution orders for specialized AI agents. The system moves AI from a passive co-pilot role to an autonomous background production service.

## System Architecture: The Four Pillars

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

### 1. The Ear (Work Event Notifier)

**Technology:** FastAPI + Uvicorn + Pydantic

**Responsibilities:**
- Secure webhook ingestion at `/webhooks/github`
- HMAC SHA256 signature verification
- Intelligent event triage and routing
- WorkItem manifest generation
- Queue initialization via GitHub API

**Security:**
- Rejects requests with invalid/missing `X-Hub-Signature-256`
- Returns 401 before parsing JSON body
- Validates against `WEBHOOK_SECRET` environment variable

### 2. The State (Work Queue)

**Philosophy:** "Markdown as a Database"

**Implementation:** GitHub Issues + Labels + Milestones

**State Machine (Label Logic):**

| Label | State | Description |
|-------|-------|-------------|
| `agent:queued` | QUEUED | Awaiting available Sentinel |
| `agent:in-progress` | IN_PROGRESS | Claimed by a Sentinel |
| `agent:reconciling` | RECONCILING | Stale task being recovered |
| `agent:success` | SUCCESS | Workflow completed successfully |
| `agent:error` | ERROR | Execution error occurred |
| `agent:infra-failure` | INFRA_FAILURE | Infrastructure failure |
| `agent:stalled-budget` | STALLED_BUDGET | Budget/token limit exceeded |

**Concurrency Control:**
- GitHub Assignees act as distributed locks
- Assign-then-verify pattern prevents race conditions
- Multiple Sentinel instances can safely coexist

### 3. The Brain (Sentinel Orchestrator)

**Technology:** Python 3.12+ Async + HTTPX + Shell Bridge

**Lifecycle:**

1. **Polling Discovery**
   - Queries GitHub Issues API every 60 seconds
   - Looks for `agent:queued` label
   - Jittered exponential backoff on rate limits (403/429)

2. **Task Claiming**
   - Assign-then-verify distributed locking
   - Posts claim comment with start time
   - Updates labels atomically

3. **Environment Management**
   - `devcontainer-opencode.sh up` - Provision infrastructure
   - `devcontainer-opencode.sh start` - Start opencode server
   - `devcontainer-opencode.sh prompt` - Execute workflow

4. **Heartbeat System**
   - Background async coroutine
   - Posts status every 5 minutes
   - Critical for long-running tasks (15+ minutes)

5. **Graceful Shutdown**
   - Handles SIGTERM/SIGINT signals
   - Finishes current task before exit
   - Closes HTTPX connection pool

### 4. The Hands (Opencode Worker)

**Technology:** DevContainer + opencode CLI + LLM

**Environment:**
- High-fidelity DevContainer from template
- Network isolation (dedicated Docker network)
- Resource constraints (2 CPUs, 4GB RAM)
- Ephemeral credentials

**Capabilities:**
- Reads markdown instruction modules
- Executes workflows against cloned codebase
- Runs local test suites before PR submission
- Maintains vector-indexed view of codebase

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

## Key Architectural Decisions (ADRs)

### ADR 07: Standardized Shell-Bridge Execution
- Sentinel interacts exclusively via `devcontainer-opencode.sh`
- No direct Docker SDK usage
- Guarantees environment parity with human developers

### ADR 08: Polling-First Resiliency Model
- Polling is primary discovery mechanism
- Webhooks are optimization layer
- System self-heals on restart via label reconciliation

### ADR 09: Provider-Agnostic Interface Layer
- `ITaskQueue` abstract interface
- Strategy Pattern for queue backend
- GitHub can be swapped for Linear, Jira, etc.

## Security Model

### Network Isolation
- Worker containers in dedicated Docker network
- Cannot access host network or local subnet
- Internet access for package fetching only

### Credential Management
- GitHub Installation Tokens injected as temp env vars
- Never written to disk in container
- Destroyed on container exit

### Credential Scrubbing
- Regex-based `scrub_secrets()` utility
- Strips: `ghp_*`, `ghs_*`, `gho_*`, `github_pat_*`, `Bearer`, `sk-*`, ZhipuAI keys
- Applied before posting to GitHub comments

### Resource Constraints
- Worker containers capped at 2 CPUs, 4GB RAM
- Prevents DoS from rogue agents

## Self-Bootstrapping Lifecycle

1. **Stage 0 (Seeding):** Manual clone of template repo
2. **Stage 1 (Manual Launch):** Run `devcontainer-opencode.sh up`
3. **Stage 2 (Project Setup):** Run `orchestrate-project-setup` workflow
4. **Stage 3 (Handover):** Start Sentinel service, AI manages itself

## Unified Data Model

```python
class TaskType(str, Enum):
    PLAN = "PLAN"        # Create application plan
    IMPLEMENT = "IMPLEMENT"  # Implement features
    BUGFIX = "BUGFIX"    # Fix bugs

class WorkItem(BaseModel):
    id: str              # GitHub issue ID
    issue_number: int    # Issue number
    source_url: str      # Issue URL
    context_body: str    # Issue body
    target_repo_slug: str  # owner/repo
    task_type: TaskType  # Work type
    status: WorkItemStatus  # Current state
    node_id: str         # GraphQL node ID
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| GitHub API Rate Limiting | GitHub App tokens (5,000/hr), caching, backoff |
| LLM Looping/Hallucination | Max steps timeout, cost guardrails, retry counter |
| Concurrency Collisions | Assign-then-verify locking pattern |
| Container Drift | Stop container between tasks |
| Security Injection | HMAC validation, credential scrubbing |
