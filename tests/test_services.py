"""Tests for the notifier service FastAPI application."""

import os

import pytest


# Set env vars BEFORE importing the notifier module
# (notifier validates env vars at import time)
@pytest.fixture(autouse=True, scope="module")
def _set_notifier_env():
    old_webhook = os.environ.get("WEBHOOK_SECRET")
    old_token = os.environ.get("GITHUB_TOKEN")
    os.environ["WEBHOOK_SECRET"] = "test-webhook-secret-for-testing"
    os.environ["GITHUB_TOKEN"] = "FAKE-KEY-FOR-TESTING-00000000"
    yield
    # Restore
    if old_webhook is None:
        os.environ.pop("WEBHOOK_SECRET", None)
    else:
        os.environ["WEBHOOK_SECRET"] = old_webhook
    if old_token is None:
        os.environ.pop("GITHUB_TOKEN", None)
    else:
        os.environ["GITHUB_TOKEN"] = old_token


class TestNotifierModule:
    """Tests for the notifier module structure."""

    def test_notifier_importable(self):
        from src import notifier_service

        assert hasattr(notifier_service, "app")

    def test_notifier_has_main(self):
        from src import notifier_service

        assert hasattr(notifier_service, "main")

    def test_notifier_has_health_endpoint(self):
        from src.notifier_service import app

        # FastAPI app should have routes
        routes = [r.path for r in app.routes]
        assert "/health" in routes

    def test_notifier_has_webhook_endpoint(self):
        from src.notifier_service import app

        routes = [r.path for r in app.routes]
        assert "/webhooks/github" in routes


class TestSentinelModule:
    """Tests for the sentinel module structure."""

    def test_sentinel_importable(self):
        from src import orchestrator_sentinel

        assert hasattr(orchestrator_sentinel, "Sentinel")

    def test_sentinel_has_main(self):
        from src import orchestrator_sentinel

        assert hasattr(orchestrator_sentinel, "main")
