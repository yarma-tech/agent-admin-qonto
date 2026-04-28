"""Tests for the auth dependency."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("QONTO_ORGANIZATION_SLUG", "test-slug")
os.environ.setdefault("QONTO_SECRET_KEY", "test-secret")
os.environ.setdefault("SHARED_TOKEN", "test-shared-token")


@pytest.fixture(scope="module")
def client():
    from src.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_missing_token_returns_401(client):
    response = client.get("/clients/")
    assert response.status_code == 401


def test_wrong_token_returns_401(client):
    response = client.get("/clients/", headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401


def test_correct_token_passes_auth(client, respx_mock=None):
    """With the correct token, the auth check passes (Qonto call will fail in tests but not 401)."""
    import unittest.mock as mock

    import httpx

    mock_response = httpx.Response(200, json={"clients": []})
    with mock.patch("httpx.AsyncClient.request", return_value=mock_response):
        response = client.get("/clients/", headers={"Authorization": "Bearer test-shared-token"})
    # 200 or any non-401 means auth passed
    assert response.status_code != 401
