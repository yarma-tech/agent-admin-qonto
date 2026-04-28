"""Async Qonto API client with automatic retry on 429 / 5xx."""

import asyncio
from typing import Any

import httpx
from fastapi import HTTPException

from src.config import settings

QONTO_BASE_URL = "https://thirdparty.qonto.com/v2"
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_RETRY_WAIT_SECONDS = 2


def _auth_header() -> str:
    return f"{settings.qonto_organization_slug}:{settings.qonto_secret_key}"


async def api_fetch(
    method: str,
    endpoint: str,
    body: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Make an authenticated request to the Qonto API.

    Retries once on 429 or 5xx responses after waiting _RETRY_WAIT_SECONDS.
    Raises HTTPException with the Qonto error details on failure.
    """
    url = f"{QONTO_BASE_URL}{endpoint}"
    headers = {
        "Authorization": _auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Filter out None query params
    params = {k: v for k, v in (query or {}).items() if v is not None}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(2):  # 0 = first try, 1 = retry
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params or None,
                json=body,
            )

            if response.status_code < 400:
                if response.content:
                    return response.json()
                return {}

            # Retry on rate-limit or server errors (first attempt only)
            if attempt == 0 and response.status_code in _RETRY_STATUSES:
                await asyncio.sleep(_RETRY_WAIT_SECONDS)
                continue

            # Parse Qonto error payload when available
            detail: Any = f"Qonto API error {response.status_code}"
            try:
                payload = response.json()
                if "errors" in payload:
                    detail = payload["errors"]
                elif "error" in payload:
                    detail = payload["error"]
                else:
                    detail = payload
            except Exception:
                detail = response.text or detail

            raise HTTPException(status_code=response.status_code, detail=detail)

    # Should never reach here, but satisfy the type checker
    raise HTTPException(status_code=502, detail="Unexpected proxy error")
