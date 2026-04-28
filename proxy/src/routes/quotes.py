from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from src.auth import verify_token
from src.qonto_client import api_fetch

router = APIRouter(prefix="/quotes", tags=["quotes"], dependencies=[Depends(verify_token)])


@router.post("/")
async def create_quote(body: dict[str, Any]) -> dict:
    return await api_fetch("POST", "/quotes", body=body)


@router.get("/")
async def list_quotes(
    client_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int | None, Query()] = None,
    per_page: Annotated[int | None, Query()] = None,
) -> dict:
    return await api_fetch(
        "GET",
        "/quotes",
        query={"client_id": client_id, "status": status, "page": page, "per_page": per_page},
    )


@router.get("/{quote_id}")
async def get_quote(quote_id: str) -> dict:
    return await api_fetch("GET", f"/quotes/{quote_id}")


@router.patch("/{quote_id}")
async def update_quote(quote_id: str, body: dict[str, Any]) -> dict:
    return await api_fetch("PATCH", f"/quotes/{quote_id}", body=body)


@router.post("/{quote_id}/send")
async def send_quote(quote_id: str, body: dict[str, Any] | None = None) -> dict:
    return await api_fetch("POST", f"/quotes/{quote_id}/send", body=body or {})
