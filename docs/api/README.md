# OS-APOW API Documentation

This directory contains API documentation for the OS-APOW system.

## Endpoints

### Health Check

```
GET /health
```

Returns the health status of the notifier service.

**Response:**
```json
{
  "status": "healthy",
  "service": "os-apow-notifier"
}
```

### GitHub Webhook

```
POST /webhooks/github
```

Receives GitHub webhook events. Requires valid `X-Hub-Signature-256` header.

**Headers:**
- `X-GitHub-Event`: Event type (issues, ping, etc.)
- `X-Hub-Signature-256`: HMAC SHA256 signature

**Supported Events:**
- `issues.opened` - Queues new issues for processing
- `ping` - Returns pong response

## Interactive Documentation

When running the notifier locally:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
