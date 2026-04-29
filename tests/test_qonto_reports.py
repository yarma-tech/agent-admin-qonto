"""Tests for qonto_reports agent tools (read-only listing and aggregation)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.websocket.protocol import WSResponse

# ---------------------------------------------------------------------------
# qonto_list_invoices
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_invoices_sends_get():
    """GET /invoices is called with default pagination params."""
    mock_response = WSResponse(
        id="any",
        status=200,
        data={"client_invoices": [], "meta": {"total_count": 0}},
    )

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_reports import qonto_list_invoices

        result = await qonto_list_invoices("tenant-1")

    call_args = mock_ws.send_command.call_args
    tenant_called, command = call_args[0]
    assert tenant_called == "tenant-1"
    assert command.method == "GET"
    assert command.endpoint == "/invoices"
    assert command.query["page"] == "1"
    assert command.query["per_page"] == "100"
    assert result == mock_response.data


@pytest.mark.asyncio
async def test_list_invoices_with_status_filter():
    """status filter is forwarded in the query params."""
    mock_response = WSResponse(
        id="any",
        status=200,
        data={"client_invoices": [], "meta": {"total_count": 0}},
    )

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_reports import qonto_list_invoices

        await qonto_list_invoices("tenant-1", status="unpaid")

    command = mock_ws.send_command.call_args[0][1]
    assert command.query["status"] == "unpaid"


@pytest.mark.asyncio
async def test_list_invoices_with_client_id_filter():
    """client_id filter is forwarded when provided."""
    mock_response = WSResponse(id="any", status=200, data={"client_invoices": []})

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_reports import qonto_list_invoices

        await qonto_list_invoices("tenant-1", client_id="client-abc")

    command = mock_ws.send_command.call_args[0][1]
    assert command.query["client_id"] == "client-abc"


@pytest.mark.asyncio
async def test_list_invoices_no_optional_filters_in_query():
    """When no filters are given, status and client_id keys are absent."""
    mock_response = WSResponse(id="any", status=200, data={"client_invoices": []})

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_reports import qonto_list_invoices

        await qonto_list_invoices("tenant-1")

    command = mock_ws.send_command.call_args[0][1]
    assert "status" not in command.query
    assert "client_id" not in command.query


@pytest.mark.asyncio
async def test_list_invoices_returns_error_on_proxy_error():
    """Error from ws_manager is surfaced as {"error": ...}."""
    mock_response = WSResponse(id="any", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_reports import qonto_list_invoices

        result = await qonto_list_invoices("tenant-1")

    assert "error" in result
    assert result["error"] == "Proxy not connected"


# ---------------------------------------------------------------------------
# qonto_list_quotes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_quotes_sends_get():
    """GET /quotes is called with default pagination params."""
    mock_response = WSResponse(
        id="any",
        status=200,
        data={"quotes": [], "meta": {"total_count": 0}},
    )

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_reports import qonto_list_quotes

        result = await qonto_list_quotes("tenant-1")

    call_args = mock_ws.send_command.call_args
    tenant_called, command = call_args[0]
    assert tenant_called == "tenant-1"
    assert command.method == "GET"
    assert command.endpoint == "/quotes"
    assert command.query["page"] == "1"
    assert command.query["per_page"] == "100"
    assert result == mock_response.data


@pytest.mark.asyncio
async def test_list_quotes_with_status_filter():
    """status filter is forwarded for quotes."""
    mock_response = WSResponse(id="any", status=200, data={"quotes": []})

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_reports import qonto_list_quotes

        await qonto_list_quotes("tenant-1", status="pending")

    command = mock_ws.send_command.call_args[0][1]
    assert command.query["status"] == "pending"


@pytest.mark.asyncio
async def test_list_quotes_returns_error_on_proxy_error():
    """Error from ws_manager is surfaced as {"error": ...} for quotes."""
    mock_response = WSResponse(id="any", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=mock_response)

        from src.agent.tools.qonto_reports import qonto_list_quotes

        result = await qonto_list_quotes("tenant-1")

    assert result == {"error": "Proxy not connected"}


# ---------------------------------------------------------------------------
# qonto_pending_payments
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pending_payments_calculates_total():
    """Grand total aggregates unpaid invoices and pending quotes correctly."""
    invoices_data = {
        "client_invoices": [
            {"total_amount": {"value": "150.00"}},
            {"total_amount": {"value": "250.50"}},
        ]
    }
    quotes_data = {
        "quotes": [
            {"total_amount": {"value": "500.00"}},
        ]
    }

    invoice_response = WSResponse(id="i", status=200, data=invoices_data)
    quote_response = WSResponse(id="q", status=200, data=quotes_data)

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(side_effect=[invoice_response, quote_response])

        from src.agent.tools.qonto_reports import qonto_pending_payments

        result = await qonto_pending_payments("tenant-1")

    assert result["unpaid_invoices_count"] == 2
    assert result["unpaid_invoices_total"] == pytest.approx(400.50)
    assert result["pending_quotes_count"] == 1
    assert result["pending_quotes_total"] == pytest.approx(500.00)
    assert result["grand_total"] == pytest.approx(900.50)


@pytest.mark.asyncio
async def test_pending_payments_empty_lists():
    """Zero totals when both lists are empty."""
    invoice_response = WSResponse(id="i", status=200, data={"client_invoices": []})
    quote_response = WSResponse(id="q", status=200, data={"quotes": []})

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(side_effect=[invoice_response, quote_response])

        from src.agent.tools.qonto_reports import qonto_pending_payments

        result = await qonto_pending_payments("tenant-1")

    assert result["unpaid_invoices_count"] == 0
    assert result["unpaid_invoices_total"] == 0.0
    assert result["pending_quotes_count"] == 0
    assert result["pending_quotes_total"] == 0.0
    assert result["grand_total"] == 0.0


@pytest.mark.asyncio
async def test_pending_payments_handles_invoice_proxy_error():
    """Error on invoices call is propagated immediately."""
    invoice_response = WSResponse(id="i", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=invoice_response)

        from src.agent.tools.qonto_reports import qonto_pending_payments

        result = await qonto_pending_payments("tenant-1")

    assert "error" in result
    assert result["error"] == "Proxy not connected"
    # Only one call should have been made (quotes call skipped)
    assert mock_ws.send_command.call_count == 1


@pytest.mark.asyncio
async def test_pending_payments_handles_quotes_proxy_error():
    """Error on quotes call is propagated after invoices succeed."""
    invoice_response = WSResponse(id="i", status=200, data={"client_invoices": []})
    quote_response = WSResponse(id="q", status=503, error="Proxy not connected")

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(side_effect=[invoice_response, quote_response])

        from src.agent.tools.qonto_reports import qonto_pending_payments

        result = await qonto_pending_payments("tenant-1")

    assert "error" in result
    assert result["error"] == "Proxy not connected"


@pytest.mark.asyncio
async def test_pending_payments_calls_correct_statuses():
    """qonto_pending_payments uses status=unpaid for invoices, status=pending for quotes."""
    invoice_response = WSResponse(id="i", status=200, data={"client_invoices": []})
    quote_response = WSResponse(id="q", status=200, data={"quotes": []})

    with patch("src.agent.tools.qonto_reports.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(side_effect=[invoice_response, quote_response])

        from src.agent.tools.qonto_reports import qonto_pending_payments

        await qonto_pending_payments("tenant-1")

    calls = mock_ws.send_command.call_args_list
    invoice_cmd = calls[0][0][1]
    quote_cmd = calls[1][0][1]

    assert invoice_cmd.endpoint == "/invoices"
    assert invoice_cmd.query["status"] == "unpaid"
    assert quote_cmd.endpoint == "/quotes"
    assert quote_cmd.query["status"] == "pending"
