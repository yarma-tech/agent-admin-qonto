"""Agent tools for the full invoice lifecycle via WebSocket proxy."""

import uuid

from src.websocket.protocol import WSCommand
from src.websocket.server import ws_manager


async def qonto_create_invoice(tenant_id: str, invoice_data: dict) -> dict:
    """Create a new draft invoice. Write operation — requires confirmation.

    invoice_data: client_id, issue_date, due_date, currency, payment_methods [{iban}], items
    Items: [{title, quantity, unit_price: {value, currency}, vat_rate}]
    Amounts as strings. VAT as decimal string ("0.20" = 20%).
    Status defaults to "draft".
    """
    invoice_data.setdefault("status", "draft")
    command = WSCommand(id=str(uuid.uuid4()), method="POST", endpoint="/invoices", body=invoice_data)
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_update_invoice(tenant_id: str, invoice_id: str, update_data: dict) -> dict:
    """Update a draft invoice. Only works on draft status.

    Refuses modification of finalized invoices.
    """
    command = WSCommand(
        id=str(uuid.uuid4()),
        method="PUT",
        endpoint=f"/invoices/{invoice_id}",
        body=update_data,
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_finalize_invoice(tenant_id: str, invoice_id: str) -> dict:
    """Finalize a draft invoice. IRREVERSIBLE — once finalized, cannot be modified.

    Write operation — requires explicit confirmation with warning.
    """
    command = WSCommand(
        id=str(uuid.uuid4()),
        method="POST",
        endpoint=f"/invoices/{invoice_id}/finalize",
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_send_invoice(tenant_id: str, invoice_id: str, send_data: dict) -> dict:
    """Send an invoice by email via Qonto.

    send_data: {send_to: [email], copy_to_self: bool}
    Write operation — requires confirmation.
    """
    command = WSCommand(
        id=str(uuid.uuid4()),
        method="POST",
        endpoint=f"/invoices/{invoice_id}/send",
        body=send_data,
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_get_invoice(tenant_id: str, invoice_id: str) -> dict:
    """Get a single invoice. Read-only."""
    command = WSCommand(
        id=str(uuid.uuid4()),
        method="GET",
        endpoint=f"/invoices/{invoice_id}",
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data
