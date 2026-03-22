# Environment Setup Guide

This document explains the environment variables required to run the OS-APOW (Open Source AI-Powered Orchestration Workflow) platform.

## Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual values in `.env`

3. **Never commit `.env` files to version control** - they are already ignored by `.gitignore`

## Environment Variables

### GitHub Configuration

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token with repo, issues, and workflow permissions | Yes | `your_github_token_here` |
| `GITHUB_REPO` | Repository name | Yes | `workflow-orchestration-queue-zulu78-a` |
| `GITHUB_ORG` | GitHub organization or user name | Yes | `intel-agency` |
| `SENTINEL_BOT_LOGIN` | Bot login for sentinel operations | Yes | `sentinel-bot[bot]` |

### Webhook Security

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `WEBHOOK_SECRET` | Secret used to validate incoming webhook payloads | Yes | (random string) |

### AI Model API Keys

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `ZHIPU_API_KEY` | ZhipuAI API key for GLM model access | Yes | (API key from ZhipuAI) |
| `KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY` | Kimi (Moonshot) API key for orchestrator agent | Yes | (API key from Moonshot) |

## GitHub Token Permissions

The `GITHUB_TOKEN` requires the following permissions:

- **repo** - Full control of private repositories
- **issues** - Read/write access to issues
- **workflow** - Update GitHub Action workflows
- **contents** - Read repository contents

## DevContainer Configuration

The DevContainer automatically inherits environment variables from your local environment. Ensure these variables are set in your shell before starting the DevContainer:

```bash
# In your ~/.bashrc or ~/.zshrc
export GITHUB_TOKEN="your_token_here"
export ZHIPU_API_KEY="your_key_here"
export KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY="your_key_here"
```

### DevContainer remoteEnv Mapping

The DevContainer configuration at `.devcontainer/devcontainer.json` maps local environment variables to the container:

```json
{
  "remoteEnv": {
    "GITHUB_TOKEN": "${localEnv:GITHUB_TOKEN}",
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${localEnv:GITHUB_TOKEN}",
    "ZHIPU_API_KEY": "${localEnv:ZHIPU_API_KEY}",
    "KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY": "${localEnv:KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY}"
  }
}
```

## Security Best Practices

1. **Never commit secrets** - The `.env` file is ignored by git
2. **Use GitHub Secrets** - Store sensitive values in GitHub repository secrets for CI/CD
3. **Rotate keys regularly** - Change API keys and tokens periodically
4. **Limit token scope** - Only grant the minimum required permissions
5. **Use environment-specific tokens** - Separate tokens for development and production

## Setting Up GitHub Secrets

For GitHub Actions workflows, configure these secrets in your repository:

1. Go to **Settings** > **Secrets and variables** > **Actions**
2. Click **New repository secret**
3. Add each required secret:
   - `GITHUB_TOKEN` (automatically provided by Actions)
   - `ZHIPU_API_KEY`
   - `KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY`

## Troubleshooting

### Token Authentication Issues

If you see authentication errors:
1. Verify your token has not expired
2. Check that the token has the required permissions
3. Ensure the token is correctly set in your environment

### DevContainer Variable Issues

If environment variables are not available in the DevContainer:
1. Verify the variables are exported in your shell
2. Restart VS Code / the DevContainer
3. Check the DevContainer logs for configuration errors

## Related Documentation

- [Architecture Guide](./architecture.md) - System architecture overview
- [Development Plan](./development-plan.md) - Development roadmap
- [Implementation Specification](./implementation-specification.md) - Technical implementation details
