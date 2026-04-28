"""Shared pytest fixtures for the proxy test suite."""

import os

import pytest
from fastapi.testclient import TestClient

# Set env vars BEFORE importing anything that reads settings
os.environ.setdefault("QONTO_ORGANIZATION_SLUG", "test-slug")
os.environ.setdefault("QONTO_SECRET_KEY", "test-secret")
os.environ.setdefault("SHARED_TOKEN", "test-shared-token")


@pytest.fixture(scope="session")
def client():
    from src.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-shared-token"}
