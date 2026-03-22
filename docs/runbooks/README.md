# OS-APOW Runbooks

Operational documentation for the OS-APOW system.

## Runbooks

- [Deployment](./deployment.md) - Deploying OS-APOW
- [Monitoring](./monitoring.md) - Monitoring and alerting
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions
- [Security Incident Response](./security-incident.md) - Security procedures

## Quick Reference

### Starting Services

```bash
# Notifier only
uv run os-apow-notifier

# Full stack with Docker
docker-compose up -d
```

### Checking Logs

```bash
# Docker logs
docker-compose logs -f notifier

# Structured logs (JSON)
# Use jq for parsing
docker-compose logs notifier | jq 'select(.level == "ERROR")'
```

### Health Check

```bash
curl http://localhost:8000/health
```
