# Remediation Guide: Test Failures

## Issue Description

Three webhook endpoint tests are failing due to missing `github_token` configuration:

```
tests/test_api/test_webhooks.py::TestWebhookEndpoint::test_ping_event
tests/test_api/test_webhooks.py::TestWebhookEndpoint::test_invalid_signature_rejected
tests/test_api/test_webhooks.py::TestWebhookEndpoint::test_unrecognized_event_ignored
```

## Root Cause

The FastAPI app is initialized with dependency injection that calls `get_settings()` at import time. The tests are attempting to mock `get_settings` after the app has already been created, causing Pydantic validation errors when the real `Settings()` is instantiated.

## Solution

Update `tests/conftest.py` to include a fixture that properly overrides FastAPI dependencies:

```python
# Add to tests/conftest.py

import os
from fastapi.testclient import TestClient
from os_apow.api.routes.webhooks import app
from os_apow.config import get_settings


@pytest.fixture
def test_client_with_mock_settings(mock_settings: Settings):
    """Create a test client with mocked settings.
    
    Args:
        mock_settings: Test settings.
        
    Returns:
        TestClient with dependency overrides.
    """
    # Override the settings dependency
    app.dependency_overrides[get_settings] = lambda: mock_settings
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()
```

Then update the failing tests to use this fixture instead of creating their own TestClient:

```python
# In tests/test_api/test_webhooks.py

class TestWebhookEndpoint:
    """Test webhook endpoint behavior."""
    
    def test_ping_event(self, test_client_with_mock_settings: TestClient) -> None:
        """Test ping event returns pong."""
        client = test_client_with_mock_settings
        payload = b'{"test": "data"}'
        secret = "test-secret"
        
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
    
    # Similar updates for other test methods...
```

## Alternative Solution

Set environment variables before importing the app in tests:

```python
# In tests/conftest.py

import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def set_test_env_vars():
    """Set test environment variables before any tests run."""
    os.environ.setdefault("OS_APOW_GITHUB_TOKEN", "FAKE-KEY-FOR-TESTING-00000000")
    os.environ.setdefault("OS_APOW_GITHUB_ORG", "test-org")
    os.environ.setdefault("OS_APOW_GITHUB_REPO", "test-repo")
    os.environ.setdefault("OS_APOW_WEBHOOK_SECRET", "test-secret")
    
    yield
    
    # Clean up (optional)
    for key in ["OS_APOW_GITHUB_TOKEN", "OS_APOW_GITHUB_ORG", "OS_APOW_GITHUB_REPO", "OS_APOW_WEBHOOK_SECRET"]:
        os.environ.pop(key, None)
```

## Verification

After applying the fix, run:

```bash
uv run pytest tests/test_api/test_webhooks.py -v
```

All 9 tests in the file should pass.

## Priority

**Medium** - This is a test configuration issue, not a code defect. The underlying webhook implementation is correct and functional. However, fixing this ensures proper test coverage for the webhook endpoints.

## Estimated Effort

**15-30 minutes** - Simple fixture update required.
