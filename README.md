# OS-APOW

> **Headless Agentic Orchestration Platform**

OS-APOW is a groundbreaking system that transforms GitHub Issues into automated execution orders for specialized AI agents. It moves AI from a passive co-pilot role to an **autonomous background production service**.

## Features

- **Secure Webhook Ingestion** - Hardened `/webhooks/github` endpoint with HMAC SHA256 validation
- **Intelligent Triaging** - Auto-detects templates (`[Application Plan]`, `[Bugfix]`) and applies labels
- **Resilient Task Polling** - Polling-first discovery with jittered exponential backoff
- **Concurrency Control** - Assign-then-verify pattern using GitHub Assignees as distributed locks
- **Shell-Bridge Execution** - Orchestrator interacts via `devcontainer-opencode.sh` CLI abstraction
- **Heartbeat System** - Posts status comments every 5 minutes for long-running tasks
- **Credential Scrubbing** - Regex-based secret redaction before posting to GitHub
- **Graceful Shutdown** - Handles SIGTERM/SIGINT, finishes current task before exit

## Architecture

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

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for worker containers)
- GitHub Personal Access Token

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/intel-agency/workflow-orchestration-queue-zulu78-a.git
   cd workflow-orchestration-queue-zulu78-a
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

4. Run the notifier:
   ```bash
   uv run os-apow-notifier
   ```

### Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f notifier
```

## Project Structure

```
workflow-orchestration-queue/
├── src/os_apow/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entrypoint
│   ├── api/
│   │   ├── routes/
│   │   │   └── webhooks.py  # GitHub webhook endpoints
│   │   └── deps.py          # Dependency injection
│   ├── models/
│   │   └── work_item.py     # WorkItem Pydantic model
│   ├── services/
│   │   ├── github_client.py # GitHub API wrapper
│   │   ├── queue.py         # GitHub-based queue logic
│   │   └── worker.py        # Sentinel worker
│   ├── config.py            # Pydantic settings
│   └── utils/
│       └── logging.py       # Structured logging setup
├── tests/
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_models/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## State Machine

| Label | State | Description |
|-------|-------|-------------|
| `agent:queued` | QUEUED | Awaiting available Sentinel |
| `agent:in-progress` | IN_PROGRESS | Claimed by a Sentinel |
| `agent:reconciling` | RECONCILING | Stale task being recovered |
| `agent:success` | SUCCESS | Workflow completed successfully |
| `agent:error` | ERROR | Execution error occurred |
| `agent:infra-failure` | INFRA_FAILURE | Infrastructure failure |
| `agent:stalled-budget` | STALLED_BUDGET | Budget/token limit exceeded |

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=os_apow

# Run specific test file
uv run pytest tests/test_api/test_webhooks.py
```

### Code Quality

```bash
# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests

# Type check
uv run mypy src
```

## API Documentation

When running the notifier, API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

All configuration is via environment variables with the `OS_APOW_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `OS_APOW_GITHUB_TOKEN` | GitHub authentication token | Required |
| `OS_APOW_GITHUB_ORG` | Organization name | Required |
| `OS_APOW_GITHUB_REPO` | Target repository | Required |
| `OS_APOW_WEBHOOK_SECRET` | HMAC secret for webhooks | Required |
| `OS_APOW_WEBHOOK_PORT` | Webhook receiver port | 8000 |
| `OS_APOW_SENTINEL_ID` | Unique sentinel identifier | sentinel-001 |
| `OS_APOW_POLL_INTERVAL_SECONDS` | Polling interval | 60 |
| `OS_APOW_LOG_LEVEL` | Logging level | INFO |
| `OS_APOW_LOG_FORMAT` | Log format (json/text) | json |

## Security

- **HMAC Validation**: All webhooks validated against `X-Hub-Signature-256`
- **Credential Scrubbing**: Secrets automatically redacted from logs and comments
- **Network Isolation**: Worker containers in dedicated Docker network
- **Resource Constraints**: Workers capped at 2 CPUs, 4GB RAM

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Documentation

- [Architecture Guide](docs/architecture/README.md)
- [API Reference](docs/api/README.md)
- [Runbooks](docs/runbooks/README.md)
