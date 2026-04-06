"""
OS-APOW Webhook Routes

FastAPI endpoints for GitHub webhook ingestion with HMAC validation.
"""

import hashlib
import hmac
import logging
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from ...config import Settings, get_settings
from ...models.work_item import TaskType, WorkItem, WorkItemStatus
from ...services.queue import GitHubQueue
from ..deps import get_github_queue

logger = logging.getLogger("os_apow.webhooks")

app = FastAPI(
    title="OS-APOW",
    description="Headless Agentic Orchestration Platform - Webhook Receiver",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


def verify_webhook_signature(
    payload: bytes,
    signature: str | None,
    secret: str,
) -> bool:
    """Verify GitHub webhook HMAC signature.

    Args:
        payload: Raw request body bytes.
        signature: X-Hub-Signature-256 header value.
        secret: Webhook secret.

    Returns:
        True if signature is valid, False otherwise.
    """
    if not signature or not secret:
        return False

    if not signature.startswith("sha256="):
        return False

    expected_sig = signature[7:]  # Remove 'sha256=' prefix
    computed_sig = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sig, computed_sig)


async def validate_webhook(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> bytes:
    """Dependency to validate webhook signature.

    Args:
        request: FastAPI request object.
        x_hub_signature_256: Signature header.
        settings: Application settings.

    Returns:
        Raw request body bytes.

    Raises:
        HTTPException: If signature is invalid.
    """
    payload = await request.body()

    if not verify_webhook_signature(payload, x_hub_signature_256, settings.webhook_secret):
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    return payload


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status.
    """
    return {"status": "healthy", "service": "os-apow-notifier"}


@app.post("/webhooks/github")
async def handle_github_webhook(
    payload: Annotated[bytes, Depends(validate_webhook)],
    x_github_event: Annotated[str, Header()],
    queue: Annotated[GitHubQueue, Depends(get_github_queue)],
) -> dict[str, Any]:
    """Handle GitHub webhook events.

    Args:
        payload: Raw webhook payload (validated).
        x_github_event: GitHub event type header.
        queue: GitHub queue instance.

    Returns:
        Response indicating action taken.

    Raises:
        HTTPException: On processing errors.
    """
    import json

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    logger.info(f"Received GitHub event: {x_github_event}")

    # Handle issues events
    if x_github_event == "issues":
        action = data.get("action", "")
        issue = data.get("issue", {})
        repository = data.get("repository", {})

        # Only process newly opened issues
        if action != "opened":
            return {"status": "ignored", "reason": f"action '{action}' not handled"}

        title = issue.get("title", "")
        body = issue.get("body", "")
        labels = [label.get("name", "") for label in issue.get("labels", [])]

        # Detect task type from title/labels
        task_type = TaskType.IMPLEMENT
        if "[Plan]" in title or "[Application Plan]" in title or "agent:plan" in labels:
            task_type = TaskType.PLAN
        elif "bug" in labels or "bugfix" in labels:
            task_type = TaskType.BUGFIX

        # Create work item
        repo_slug = repository.get("full_name", "")
        work_item = WorkItem(
            id=str(issue.get("id", "")),
            issue_number=issue.get("number", 0),
            source_url=issue.get("html_url", ""),
            context_body=body or "",
            target_repo_slug=repo_slug,
            task_type=task_type,
            status=WorkItemStatus.QUEUED,
            node_id=issue.get("node_id", ""),
        )

        # Add to queue
        success = await queue.add_to_queue(work_item)

        if success:
            logger.info(f"Queued issue #{work_item.issue_number} as {task_type.value}")
            return {
                "status": "queued",
                "issue_number": work_item.issue_number,
                "task_type": task_type.value,
            }
        else:
            logger.error(f"Failed to queue issue #{work_item.issue_number}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to queue issue",
            )

    # Handle ping events
    if x_github_event == "ping":
        return {"status": "pong", "zen": data.get("zen", "")}

    return {"status": "ignored", "event": x_github_event}
