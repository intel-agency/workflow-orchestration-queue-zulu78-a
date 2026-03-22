# OS-APOW Technology Stack

## Core Language
- **Python 3.12+** - Primary language for orchestrator, API, and system logic
  - Async capabilities with `asyncio`
  - Improved error messages and performance
  - Native type hints support

## Runtime & Package Management
- **uv** - Rust-based Python package manager (replaces pip/poetry)
  - Orders of magnitude faster dependency resolution
  - Deterministic lockfiles (`uv.lock`)
  - Native `pyproject.toml` support

## Web Framework
- **FastAPI** - High-performance async web framework
  - Native Pydantic integration
  - Automatic OpenAPI/Swagger documentation
  - Type-safe request/response handling
  - Dependency injection system

- **Uvicorn** - ASGI server implementation
  - Lightning-fast production server
  - Hot reload for development

## Data Validation
- **Pydantic** - Data validation and settings management
  - Strict schema validation
  - Settings management via environment variables
  - JSON serialization/deserialization

## HTTP Client
- **HTTPX** - Fully asynchronous HTTP client
  - Non-blocking API calls
  - Connection pooling
  - Better throughput than `requests`

## Containerization
- **Docker** - Container runtime
  - Network isolation for worker containers
  - Resource constraints (2 CPUs, 4GB RAM)
  - Ephemeral credential injection

- **DevContainers** - Reproducible development environments
  - Identical to human developer environment
  - Volume mounts for persistence
  - SSH-agent forwarding

## Shell & Scripts
- **PowerShell Core (pwsh)** - Cross-platform scripting
  - Auth synchronization scripts
  - GitHub CLI integration

- **Bash** - Shell bridge scripts
  - `devcontainer-opencode.sh` - Core orchestrator

## AI/LLM Integration
- **opencode CLI** - AI agent runtime
  - Model support: GLM-5, Claude, etc.
  - MCP server integration
  - Markdown-based instruction modules

## Observability
- **Structured Logging** - Python `logging` module
  - JSON-structured logs
  - Unique sentinel ID tracking
  - StreamHandler for stdout (Docker capture)

## State Management
- **GitHub Issues** - "Markdown as Database"
  - Labels as state machine
  - Comments for audit trail
  - Assignees as distributed locks

## Security
- **HMAC SHA256** - Webhook signature verification
- **Credential Scrubbing** - Regex-based secret redaction
- **Network Isolation** - Dedicated Docker network

## Configuration
- **Environment Variables** - Required configuration
  - `GITHUB_TOKEN` - GitHub authentication
  - `GITHUB_ORG` - Organization name
  - `SENTINEL_BOT_LOGIN` - Bot account for locking
  - `WEBHOOK_SECRET` - HMAC secret

## Project Structure
```
workflow-orchestration-queue/
├── pyproject.toml           # uv dependencies and metadata
├── uv.lock                  # Deterministic lockfile
├── src/
│   ├── notifier_service.py  # FastAPI webhook receiver
│   ├── orchestrator_sentinel.py  # Background polling service
│   ├── models/
│   │   ├── work_item.py     # Unified data model
│   │   └── github_events.py # Webhook payload schemas
│   └── queue/
│       └── github_queue.py  # ITaskQueue + GitHub implementation
├── scripts/
│   ├── devcontainer-opencode.sh  # Shell bridge
│   ├── gh-auth.ps1          # GitHub auth helper
│   └── update-remote-indices.ps1 # Vector index sync
├── local_ai_instruction_modules/  # Markdown workflow prompts
│   ├── create-app-plan.md
│   ├── perform-task.md
│   └── recover-from-error.md
└── docs/                    # Architecture and user documentation
```
