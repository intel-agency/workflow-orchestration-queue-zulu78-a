"""
OS-APOW Main Application Entry Point

Provides entry points for both the Notifier (FastAPI webhook receiver)
and the Sentinel (background polling service).
"""

import logging

from .config import get_settings
from .utils.logging import setup_logging

logger = logging.getLogger("os_apow")


def run_notifier() -> None:
    """Run the FastAPI webhook receiver (The Ear).

    This is the primary entry point for the notifier service.
    """
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    logger.info(f"Starting OS-APOW Notifier on port {settings.webhook_port}")

    import uvicorn

    from .api.routes.webhooks import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.webhook_port,
        log_config=None,  # Use our custom logging
    )


def run_sentinel() -> None:
    """Run the Sentinel background polling service (The Brain).

    This is the primary entry point for the sentinel orchestrator.
    """
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    logger.info(f"Starting OS-APOW Sentinel ({settings.sentinel_id})")

    # TODO: Implement sentinel service in Phase 1
    raise NotImplementedError("Sentinel service implementation pending - Phase 1")


if __name__ == "__main__":
    run_notifier()
