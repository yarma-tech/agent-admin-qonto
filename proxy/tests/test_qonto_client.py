"""Tests for the Qonto API client (api_fetch)."""

import os
import unittest.mock as mock

import httpx
import pytest

os.environ.setdefault("QONTO_ORGANIZATION_SLUG", "test-slug")
os.environ.setdefault("QONTO_SECRET_KEY", "test-secret")
os.environ.setdefault("SHARED_TOKEN", "test-shared-token")

from src.qonto_client import QONTO_BASE_URL, api_fetch  # noqa: E402


def _mock_response(
    status_code: int, json_body: dict | None = None, text: str = ""
) -> httpx.Response:
    if json_body is not None:
        return httpx.Response(status_code, json=json_body)
    return httpx.Response(status_code, text=text)


@pytest.mark.asyncio
async def test_successful_get_returns_json():
    payload = {"organization": {"id": "abc"}}
    mock_resp = _mock_response(200, payload)

    with mock.patch("httpx.AsyncClient.request", return_value=mock_resp) as m:
        result = await api_fetch("GET", "/organization")

    assert result == payload
    m.assert_called_once()


@pytest.mark.asyncio
async def test_auth_header_is_slug_colon_secret():
    mock_resp = _mock_response(200, {})

    with mock.patch("httpx.AsyncClient.request", return_value=mock_resp) as m:
        await api_fetch("GET", "/organization")

    call_kwargs = m.call_args.kwargs
    headers = call_kwargs["headers"]
    assert headers["Authorization"] == "test-slug:test-secret"


@pytest.mark.asyncio
async def test_retries_once_on_429_then_succeeds():
    call_count = 0

    async def fake_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_response(429, {"error": "rate limited"})
        return _mock_response(200, {"ok": True})

    with mock.patch("httpx.AsyncClient.request", side_effect=fake_request):
        with mock.patch("asyncio.sleep", return_value=None) as sleep_mock:
            result = await api_fetch("GET", "/organization")

    assert call_count == 2
    assert result == {"ok": True}
    sleep_mock.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_retries_once_on_503_then_succeeds():
    call_count = 0

    async def fake_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_response(503, {"error": "unavailable"})
        return _mock_response(200, {"data": "value"})

    with mock.patch("httpx.AsyncClient.request", side_effect=fake_request):
        with mock.patch("asyncio.sleep", return_value=None):
            result = await api_fetch("GET", "/organization")

    assert call_count == 2
    assert result == {"data": "value"}


@pytest.mark.asyncio
async def test_raises_http_exception_on_404():
    from fastapi import HTTPException

    mock_resp = _mock_response(404, {"errors": [{"code": "not_found"}]})

    with mock.patch("httpx.AsyncClient.request", return_value=mock_resp):
        with pytest.raises(HTTPException) as exc_info:
            await api_fetch("GET", "/quotes/nonexistent")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == [{"code": "not_found"}]


@pytest.mark.asyncio
async def test_raises_http_exception_after_two_429s():
    from fastapi import HTTPException

    rate_limited = _mock_response(429, {"error": "rate limited"})
    with mock.patch("httpx.AsyncClient.request", return_value=rate_limited):
        with mock.patch("asyncio.sleep", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await api_fetch("GET", "/quotes")

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_query_params_passed_correctly():
    mock_resp = _mock_response(200, {"quotes": []})

    with mock.patch("httpx.AsyncClient.request", return_value=mock_resp) as m:
        await api_fetch("GET", "/quotes", query={"page": 2, "per_page": 25, "status": None})

    call_kwargs = m.call_args.kwargs
    # None values should be filtered out
    assert call_kwargs["params"] == {"page": 2, "per_page": 25}


@pytest.mark.asyncio
async def test_post_with_body():
    mock_resp = _mock_response(201, {"quote": {"id": "q1"}})

    with mock.patch("httpx.AsyncClient.request", return_value=mock_resp) as m:
        result = await api_fetch("POST", "/quotes", body={"title": "Test"})

    call_kwargs = m.call_args.kwargs
    assert call_kwargs["json"] == {"title": "Test"}
    assert call_kwargs["method"] == "POST"
    assert result == {"quote": {"id": "q1"}}


@pytest.mark.asyncio
async def test_empty_response_body_returns_empty_dict():
    mock_resp = httpx.Response(204)  # No content

    with mock.patch("httpx.AsyncClient.request", return_value=mock_resp):
        result = await api_fetch("DELETE", "/quotes/q1")

    assert result == {}


@pytest.mark.asyncio
async def test_base_url_used():
    mock_resp = _mock_response(200, {})

    with mock.patch("httpx.AsyncClient.request", return_value=mock_resp) as m:
        await api_fetch("GET", "/organization")

    call_kwargs = m.call_args.kwargs
    assert call_kwargs["url"] == f"{QONTO_BASE_URL}/organization"
