"""Read-only agent tools for listing invoices, quotes, and pending payments."""

import uuid

from src.websocket.protocol import WSCommand
from src.websocket.server import ws_manager


async def qonto_list_invoices(
    tenant_id: str,
    status: str | None = None,
    client_id: str | None = None,
    page: int = 1,
) -> dict:
    """List invoices with optional filters. Read-only — no confirmation needed."""
    query = {"page": str(page), "per_page": "100"}
    if status:
        query["status"] = status
    if client_id:
        query["client_id"] = client_id

    command = WSCommand(
        id=str(uuid.uuid4()),
        method="GET",
        endpoint="/invoices",
        query=query,
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_list_quotes(
    tenant_id: str,
    status: str | None = None,
    client_id: str | None = None,
    page: int = 1,
) -> dict:
    """List quotes with optional filters. Read-only."""
    query = {"page": str(page), "per_page": "100"}
    if status:
        query["status"] = status
    if client_id:
        query["client_id"] = client_id

    command = WSCommand(
        id=str(uuid.uuid4()),
        method="GET",
        endpoint="/quotes",
        query=query,
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_pending_payments(tenant_id: str) -> dict:
    """Calculate total pending payments: unpaid invoices + validated quotes not yet invoiced.

    Read-only — no confirmation needed.
    """
    # Get unpaid invoices
    invoices_result = await qonto_list_invoices(tenant_id, status="unpaid")
    if "error" in invoices_result:
        return invoices_result

    # Get pending/validated quotes
    quotes_result = await qonto_list_quotes(tenant_id, status="pending")
    if "error" in quotes_result:
        return quotes_result

    # Calculate totals
    invoice_total = sum(
        float(inv.get("total_amount", {}).get("value", "0")) for inv in invoices_result.get("client_invoices", [])
    )
    quote_total = sum(float(q.get("total_amount", {}).get("value", "0")) for q in quotes_result.get("quotes", []))

    return {
        "unpaid_invoices_count": len(invoices_result.get("client_invoices", [])),
        "unpaid_invoices_total": invoice_total,
        "pending_quotes_count": len(quotes_result.get("quotes", [])),
        "pending_quotes_total": quote_total,
        "grand_total": invoice_total + quote_total,
    }
