"""Agent tools for Qonto quote lifecycle management via WebSocket proxy."""

import uuid

from src.websocket.protocol import WSCommand
from src.websocket.server import ws_manager


async def qonto_create_quote(tenant_id: str, quote_data: dict) -> dict:
    """Create a new quote. Write operation — requires user confirmation.

    quote_data should contain: client_id, issue_date, expiry_date, currency, items
    Items format: [{title, quantity, unit_price: {value, currency}, vat_rate, description?, discount?}]
    Amounts must be strings ("800.00"). VAT as decimal fraction string ("0.085" = 8.5%).
    Don't send 'number' — Qonto auto-generates it.
    """
    command = WSCommand(id=str(uuid.uuid4()), method="POST", endpoint="/quotes", body=quote_data)
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_update_quote(tenant_id: str, quote_id: str, update_data: dict) -> dict:
    """Update a draft quote. Only works on draft/pending_approval status.
    Refuses modification of sent quotes."""
    command = WSCommand(id=str(uuid.uuid4()), method="PATCH", endpoint=f"/quotes/{quote_id}", body=update_data)
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_send_quote(tenant_id: str, quote_id: str, send_data: dict) -> dict:
    """Send a quote by email via Qonto infrastructure.
    send_data: {send_to: [email], copy_to_self: bool}
    Write operation — requires user confirmation."""
    command = WSCommand(id=str(uuid.uuid4()), method="POST", endpoint=f"/quotes/{quote_id}/send", body=send_data)
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_validate_quote(tenant_id: str, quote_id: str) -> dict:
    """Validate a quote → creates a draft invoice from quote items.
    Write operation — requires user confirmation."""
    # First, get the quote details
    get_command = WSCommand(id=str(uuid.uuid4()), method="GET", endpoint=f"/quotes/{quote_id}")
    quote_response = await ws_manager.send_command(tenant_id, get_command)
    if quote_response.error:
        return {"error": quote_response.error}

    quote = quote_response.data
    if isinstance(quote, dict) and "quote" in quote:
        quote = quote["quote"]

    # Create draft invoice from quote items
    invoice_data = {
        "client_id": quote.get("client_id"),
        "issue_date": quote.get("issue_date"),
        "due_date": quote.get("expiry_date"),
        "currency": quote.get("currency", "EUR"),
        "items": quote.get("items", []),
        "status": "draft",
    }
    if quote.get("discount"):
        invoice_data["discount"] = quote["discount"]

    create_command = WSCommand(id=str(uuid.uuid4()), method="POST", endpoint="/invoices", body=invoice_data)
    invoice_response = await ws_manager.send_command(tenant_id, create_command)
    if invoice_response.error:
        return {"error": invoice_response.error}

    return {
        "validated": True,
        "quote_id": quote_id,
        "invoice": invoice_response.data,
    }


async def qonto_list_quotes(tenant_id: str, **filters) -> dict:
    """List quotes. Read-only — no confirmation needed."""
    query = {k: str(v) for k, v in filters.items() if v is not None}
    query.setdefault("per_page", "100")
    command = WSCommand(id=str(uuid.uuid4()), method="GET", endpoint="/quotes", query=query)
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_get_quote(tenant_id: str, quote_id: str) -> dict:
    """Get a single quote by ID. Read-only."""
    command = WSCommand(id=str(uuid.uuid4()), method="GET", endpoint=f"/quotes/{quote_id}")
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data
