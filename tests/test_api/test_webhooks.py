"""
Tests for OS-APOW Webhook Routes
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from os_apow.api.routes.webhooks import app, verify_webhook_signature
from os_apow.models.work_item import WorkItemStatus


class TestWebhookSignature:
    """Tests for webhook signature validation."""

    def test_valid_signature(self) -> None:
        """Test that valid signature passes validation."""
        secret = "test-secret"
        payload = b'{"test": "data"}'
        signature = (
            "sha256="
            + hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()
        )

        assert verify_webhook_signature(payload, signature, secret) is True

    def test_invalid_signature(self) -> None:
        """Test that invalid signature fails validation."""
        payload = b'{"test": "data"}'
        signature = "sha256=invalid"

        assert verify_webhook_signature(payload, signature, "test-secret") is False

    def test_missing_signature(self) -> None:
        """Test that missing signature fails validation."""
        payload = b'{"test": "data"}'

        assert verify_webhook_signature(payload, None, "test-secret") is False

    def test_missing_secret(self) -> None:
        """Test that missing secret fails validation."""
        payload = b'{"test": "data"}'
        signature = "sha256=somehash"

        assert verify_webhook_signature(payload, signature, "") is False

    def test_wrong_hash_prefix(self) -> None:
        """Test that wrong hash prefix fails validation."""
        payload = b'{"test": "data"}'
        signature = "sha1=somehash"

        assert verify_webhook_signature(payload, signature, "test-secret") is False


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self) -> None:
        """Test health check returns healthy status."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "os-apow-notifier"


class TestWebhookEndpoint:
    """Tests for GitHub webhook endpoint."""

    def _create_signature(self, payload: bytes, secret: str) -> str:
        """Create a valid signature for testing."""
        return (
            "sha256="
            + hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()
        )

    def test_ping_event(self) -> None:
        """Test handling of ping event."""
        client = TestClient(app)
        payload = b'{"zen": "Keep it simple"}'
        secret = "test-secret"

        with patch("os_apow.api.routes.webhooks.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.webhook_secret = secret
            mock_get_settings.return_value = mock_settings

            response = client.post(
                "/webhooks/github",
                content=payload,
                headers={
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": self._create_signature(payload, secret),
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pong"

    def test_invalid_signature_rejected(self) -> None:
        """Test that invalid signature is rejected with 401."""
        client = TestClient(app)
        payload = b'{"test": "data"}'

        with patch("os_apow.api.routes.webhooks.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.webhook_secret = "test-secret"
            mock_get_settings.return_value = mock_settings

            response = client.post(
                "/webhooks/github",
                content=payload,
                headers={
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": "sha256=invalid",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 401

    def test_unrecognized_event_ignored(self) -> None:
        """Test that unrecognized events are ignored."""
        client = TestClient(app)
        payload = b'{"test": "data"}'
        secret = "test-secret"

        with patch("os_apow.api.routes.webhooks.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.webhook_secret = secret
            mock_get_settings.return_value = mock_settings

            response = client.post(
                "/webhooks/github",
                content=payload,
                headers={
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": self._create_signature(payload, secret),
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
