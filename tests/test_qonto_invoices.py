"""Tests for qonto_invoices agent tools (full invoice lifecycle)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.websocket.protocol import WSResponse

# ---------------------------------------------------------------------------
# qonto_create_invoice
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_invoice_sends_post_with_draft_default():
    """POST /invoices is called and status defaults to 'draft'."""
    mock_response = WSResponse(id="any", status=200, data={"id": "inv-1", "status": "draft"})

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_create_invoice

        invoice_data = {
            "client_id": "client-abc",
            "issue_date": "2026-04-28",
            "due_date": "2026-05-28",
            "currency": "EUR",
            "payment_methods": [{"iban": "FR7630006000011234567890189"}],
            "items": [
                {
                    "title": "Consulting",
                    "quantity": 1,
                    "unit_price": {"value": "1000.00", "currency": "EUR"},
                    "vat_rate": "0.20",
                }
            ],
        }
        result = await qonto_create_invoice("tenant-1", invoice_data)

    tenant_called, command = mock_ws.send_command.call_args[0]
    assert tenant_called == "tenant-1"
    assert command.method == "POST"
    assert command.endpoint == "/invoices"
    assert command.body["status"] == "draft"
    assert result == {"id": "inv-1", "status": "draft"}


@pytest.mark.asyncio
async def test_create_invoice_preserves_explicit_status():
    """An explicit status in invoice_data is not overwritten."""
    mock_response = WSResponse(id="any", status=200, data={"id": "inv-2", "status": "finalized"})

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_create_invoice

        invoice_data = {"client_id": "client-abc", "status": "finalized"}
        result = await qonto_create_invoice("tenant-1", invoice_data)

    command = mock_ws.send_command.call_args[0][1]
    assert command.body["status"] == "finalized"
    assert result == {"id": "inv-2", "status": "finalized"}


@pytest.mark.asyncio
async def test_create_invoice_error_propagation():
    """Error response from ws_manager is returned as {'error': ...}."""
    mock_response = WSResponse(id="any", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_create_invoice

        result = await qonto_create_invoice("tenant-1", {"client_id": "client-abc"})

    assert result == {"error": "Proxy not connected"}


# ---------------------------------------------------------------------------
# qonto_update_invoice
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_invoice_sends_put():
    """PUT /invoices/{id} is called with the update body."""
    mock_response = WSResponse(id="any", status=200, data={"id": "inv-1", "due_date": "2026-06-01"})

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_update_invoice

        result = await qonto_update_invoice("tenant-1", "inv-1", {"due_date": "2026-06-01"})

    tenant_called, command = mock_ws.send_command.call_args[0]
    assert tenant_called == "tenant-1"
    assert command.method == "PUT"
    assert command.endpoint == "/invoices/inv-1"
    assert command.body == {"due_date": "2026-06-01"}
    assert result == {"id": "inv-1", "due_date": "2026-06-01"}


@pytest.mark.asyncio
async def test_update_invoice_error_propagation():
    """Error from ws_manager is surfaced as {'error': ...}."""
    mock_response = WSResponse(id="any", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_update_invoice

        result = await qonto_update_invoice("tenant-1", "inv-1", {"due_date": "2026-06-01"})

    assert result == {"error": "Proxy not connected"}


# ---------------------------------------------------------------------------
# qonto_finalize_invoice
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_finalize_invoice_sends_post():
    """POST /invoices/{id}/finalize is called with no body."""
    mock_response = WSResponse(id="any", status=200, data={"id": "inv-1", "status": "finalized"})

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_finalize_invoice

        result = await qonto_finalize_invoice("tenant-1", "inv-1")

    tenant_called, command = mock_ws.send_command.call_args[0]
    assert tenant_called == "tenant-1"
    assert command.method == "POST"
    assert command.endpoint == "/invoices/inv-1/finalize"
    assert result == {"id": "inv-1", "status": "finalized"}


@pytest.mark.asyncio
async def test_finalize_invoice_error_propagation():
    """Error from ws_manager is surfaced as {'error': ...}."""
    mock_response = WSResponse(id="any", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_finalize_invoice

        result = await qonto_finalize_invoice("tenant-1", "inv-1")

    assert result == {"error": "Proxy not connected"}


# ---------------------------------------------------------------------------
# qonto_send_invoice
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_invoice_sends_post_with_body():
    """POST /invoices/{id}/send is called with send_data as body."""
    mock_response = WSResponse(id="any", status=200, data={"sent": True})

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_send_invoice

        send_data = {"send_to": ["client@example.com"], "copy_to_self": True}
        result = await qonto_send_invoice("tenant-1", "inv-1", send_data)

    tenant_called, command = mock_ws.send_command.call_args[0]
    assert tenant_called == "tenant-1"
    assert command.method == "POST"
    assert command.endpoint == "/invoices/inv-1/send"
    assert command.body == {"send_to": ["client@example.com"], "copy_to_self": True}
    assert result == {"sent": True}


@pytest.mark.asyncio
async def test_send_invoice_error_propagation():
    """Error from ws_manager is surfaced as {'error': ...}."""
    mock_response = WSResponse(id="any", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_send_invoice

        result = await qonto_send_invoice("tenant-1", "inv-1", {"send_to": ["x@x.com"]})

    assert result == {"error": "Proxy not connected"}


# ---------------------------------------------------------------------------
# qonto_get_invoice
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_invoice_sends_get():
    """GET /invoices/{id} is called for a single invoice lookup."""
    invoice_payload = {"id": "inv-1", "status": "finalized", "total_amount": {"value": "1200.00"}}
    mock_response = WSResponse(id="any", status=200, data=invoice_payload)

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_get_invoice

        result = await qonto_get_invoice("tenant-1", "inv-1")

    tenant_called, command = mock_ws.send_command.call_args[0]
    assert tenant_called == "tenant-1"
    assert command.method == "GET"
    assert command.endpoint == "/invoices/inv-1"
    assert result == invoice_payload


@pytest.mark.asyncio
async def test_get_invoice_error_propagation():
    """Error from ws_manager is surfaced as {'error': ...}."""
    mock_response = WSResponse(id="any", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_invoices.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_invoices import qonto_get_invoice

        result = await qonto_get_invoice("tenant-1", "inv-1")

    assert result == {"error": "Proxy not connected"}
