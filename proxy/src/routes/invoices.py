from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from src.auth import verify_token
from src.qonto_client import api_fetch

router = APIRouter(prefix="/invoices", tags=["invoices"], dependencies=[Depends(verify_token)])

_ENDPOINT = "/client_invoices"


@router.post("/")
async def create_invoice(body: dict[str, Any]) -> dict:
    return await api_fetch("POST", _ENDPOINT, body=body)


@router.get("/")
async def list_invoices(
    status: Annotated[str | None, Query()] = None,
    client_id: Annotated[str | None, Query()] = None,
    page: Annotated[int | None, Query()] = None,
    per_page: Annotated[int | None, Query()] = None,
) -> dict:
    return await api_fetch(
        "GET",
        _ENDPOINT,
        query={"status": status, "client_id": client_id, "page": page, "per_page": per_page},
    )


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str) -> dict:
    return await api_fetch("GET", f"{_ENDPOINT}/{invoice_id}")


@router.put("/{invoice_id}")
async def update_invoice(invoice_id: str, body: dict[str, Any]) -> dict:
    """Update a draft invoice."""
    return await api_fetch("PUT", f"{_ENDPOINT}/{invoice_id}", body=body)


@router.post("/{invoice_id}/finalize")
async def finalize_invoice(invoice_id: str, body: dict[str, Any] | None = None) -> dict:
    return await api_fetch("POST", f"{_ENDPOINT}/{invoice_id}/finalize", body=body or {})


@router.post("/{invoice_id}/send")
async def send_invoice(invoice_id: str, body: dict[str, Any] | None = None) -> dict:
    return await api_fetch("POST", f"{_ENDPOINT}/{invoice_id}/send", body=body or {})
