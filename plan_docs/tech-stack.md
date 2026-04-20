# Technology Stack — OS-APOW (workflow-orchestration-queue)

> **Summary:** This document defines the technology stack for OS-APOW, a headless agentic orchestration platform that transforms GitHub Issues into automated execution orders for specialized AI agents.

---

## Core Language & Runtime

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Core Language** | Python | 3.12+ | Primary language for orchestrator, API, and system logic |
| **Package Manager** | uv | latest | Rust-based Python package manager (replaces pip/poetry) |
| **Runtime Lockfile** | uv.lock | — | Deterministic dependency resolution |

## Web Framework & API

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Web Framework** | FastAPI | High-performance async web framework for webhook receiver |
| **ASGI Server** | Uvicorn | Production ASGI server for FastAPI |
| **Data Validation** | Pydantic | Strict schema validation, settings management, and serialization |
| **API Documentation** | Swagger/OpenAPI | Auto-generated at `/docs` endpoint |

## Networking & HTTP

| Category | Technology | Purpose |
|----------|-----------|---------|
| **HTTP Client** | HTTPX | Fully asynchronous HTTP client with connection pooling for GitHub API |
| **Webhook Security** | HMAC SHA256 | Cryptographic signature verification for GitHub webhooks |

## Containerization & Infrastructure

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Containerization** | Docker | Worker container isolation and reproducible environments |
| **DevContainers** | DevContainer spec | High-fidelity development environments from template |
| **Resource Constraints** | Docker limits | 2 CPUs, 4GB RAM cap per worker container |
| **Network Isolation** | Docker networks | Dedicated network per worker for security isolation |

## Shell & Scripting

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Shell Scripts** | Bash | Core orchestrator shell bridge (`devcontainer-opencode.sh`) |
| **Utility Scripts** | PowerShell Core (pwsh) | Auth helpers, label management, index sync |

## AI/LLM Integration

| Category | Technology | Purpose |
|----------|-----------|---------|
| **AI Runtime** | opencode CLI | AI agent runtime with MCP server integration |
| **LLM Models** | GLM-5, Claude 3.5 Sonnet | Language models for code generation and reasoning |
| **MCP Servers** | sequential-thinking, memory | Model Context Protocol servers for enhanced reasoning |

## State Management

| Category | Technology | Purpose |
|----------|-----------|---------|
| **State Store** | GitHub Issues | "Markdown as Database" — labels as state machine |
| **State Machine** | GitHub Labels | `agent:queued` → `agent:in-progress` → `agent:success`/`agent:error` |
| **Distributed Locking** | GitHub Assignees | Assign-then-verify pattern for concurrency control |
| **Audit Trail** | GitHub Comments | Heartbeat updates, error logs, status transitions |

## Testing & Quality

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Test Framework** | pytest | Primary testing framework |
| **Async Testing** | pytest-asyncio | Async test support for coroutines |
| **Coverage** | pytest-cov | Code coverage reporting (target: 80%+) |
| **Linting/Formatting** | ruff | Fast Python linter and formatter |
| **Type Checking** | mypy | Static type analysis (strict mode) |

## Logging & Observability

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Logging** | Python `logging` | Structured JSON logging with unique `SENTINEL_ID` |
| **Monitoring** | Health endpoint | `/health` endpoint for service monitoring |

## CI/CD & Distribution

| Category | Technology | Purpose |
|----------|-----------|---------|
| **CI/CD** | GitHub Actions | Automated lint, scan, test, and build pipelines |
| **Container Registry** | GHCR | GitHub Container Registry for Docker images |
| **Versioning** | Semantic Versioning | Via `VERSION_PREFIX` repo variable |
| **Prebuilt Images** | DevContainer caching | `publish-docker` → `prebuild-devcontainer` pipeline |

## Security

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Webhook Validation** | HMAC SHA256 | `X-Hub-Signature-256` header verification |
| **Credential Scrubbing** | Regex-based redaction | Strips `ghp_*`, `ghs_*`, `sk-*`, Bearer tokens before posting |
| **Network Isolation** | Docker dedicated networks | Worker containers isolated from each other |
| **Token Management** | Environment variables | Tokens injected as temp env vars, never written to disk |

## Environment Variables

```env
GITHUB_TOKEN          # GitHub authentication
GITHUB_REPO           # Target repository (owner/repo)
GITHUB_ORG            # Organization name
SENTINEL_BOT_LOGIN    # Bot account for distributed locking
SENTINEL_ID           # Unique sentinel instance identifier
WEBHOOK_SECRET        # HMAC secret for webhook validation
SENTINEL_HEARTBEAT_INTERVAL  # Heartbeat interval (default: 300s)
```

## References

- [Architecture Guide v3.2](./OS-APOW%20Architecture%20Guide%20v3.2.md) — System diagrams, ADRs, data flow
- [Development Plan v4.2](./OS-APOW%20Development%20Plan%20v4.2.md) — Phased roadmap, user stories, risk assessment
- [Implementation Specification v1.2](./OS-APOW%20Implementation%20Specification%20v1.2.md) — Detailed requirements, test cases
