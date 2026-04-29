"""Tests for Qonto quotes agent tools."""

from unittest.mock import AsyncMock, patch

import pytest

from src.websocket.protocol import WSResponse

QUOTE_DATA = {
    "client_id": "client-123",
    "issue_date": "2026-04-28",
    "expiry_date": "2026-05-28",
    "currency": "EUR",
    "items": [
        {
            "title": "Consulting",
            "quantity": 2,
            "unit_price": {"value": "800.00", "currency": "EUR"},
            "vat_rate": "0.2",
        }
    ],
}

QUOTE_RESPONSE = {
    "quote": {
        "id": "quote-abc",
        "client_id": "client-123",
        "issue_date": "2026-04-28",
        "expiry_date": "2026-05-28",
        "currency": "EUR",
        "status": "draft",
        "items": [
            {
                "title": "Consulting",
                "quantity": 2,
                "unit_price": {"value": "800.00", "currency": "EUR"},
                "vat_rate": "0.2",
            }
        ],
    }
}


@pytest.mark.asyncio
async def test_create_quote_sends_post_with_correct_body():
    with patch("src.agent.tools.qonto_quotes.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=201, data=QUOTE_RESPONSE))
        from src.agent.tools.qonto_quotes import qonto_create_quote

        result = await qonto_create_quote("tenant-1", QUOTE_DATA)

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "POST"
        assert command.endpoint == "/quotes"
        assert command.body == QUOTE_DATA
        assert result == QUOTE_RESPONSE


@pytest.mark.asyncio
async def test_update_quote_sends_patch_with_correct_id():
    update_data = {"expiry_date": "2026-06-28"}
    with patch("src.agent.tools.qonto_quotes.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(
            return_value=WSResponse(id="test", status=200, data={"quote": {"id": "quote-abc", **update_data}})
        )
        from src.agent.tools.qonto_quotes import qonto_update_quote

        result = await qonto_update_quote("tenant-1", "quote-abc", update_data)

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "PATCH"
        assert command.endpoint == "/quotes/quote-abc"
        assert command.body == update_data
        assert result == {"quote": {"id": "quote-abc", **update_data}}


@pytest.mark.asyncio
async def test_send_quote_sends_post_to_send_endpoint():
    send_data = {"send_to": ["client@example.com"], "copy_to_self": True}
    with patch("src.agent.tools.qonto_quotes.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=200, data={"sent": True}))
        from src.agent.tools.qonto_quotes import qonto_send_quote

        result = await qonto_send_quote("tenant-1", "quote-abc", send_data)

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "POST"
        assert command.endpoint == "/quotes/quote-abc/send"
        assert command.body == send_data
        assert result == {"sent": True}


@pytest.mark.asyncio
async def test_validate_quote_creates_invoice_from_quote():
    invoice_response = {"invoice": {"id": "inv-xyz", "status": "draft"}}
    with patch("src.agent.tools.qonto_quotes.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(
            side_effect=[
                WSResponse(id="get", status=200, data=QUOTE_RESPONSE),
                WSResponse(id="post", status=201, data=invoice_response),
            ]
        )
        from src.agent.tools.qonto_quotes import qonto_validate_quote

        result = await qonto_validate_quote("tenant-1", "quote-abc")

        calls = mock_ws.send_command.call_args_list
        get_cmd = calls[0][0][1]
        post_cmd = calls[1][0][1]

        assert get_cmd.method == "GET"
        assert get_cmd.endpoint == "/quotes/quote-abc"

        assert post_cmd.method == "POST"
        assert post_cmd.endpoint == "/invoices"
        assert post_cmd.body["client_id"] == "client-123"
        assert post_cmd.body["due_date"] == "2026-05-28"
        assert post_cmd.body["currency"] == "EUR"
        assert post_cmd.body["status"] == "draft"

        assert result["validated"] is True
        assert result["quote_id"] == "quote-abc"
        assert result["invoice"] == invoice_response


@pytest.mark.asyncio
async def test_validate_quote_handles_get_error():
    with patch("src.agent.tools.qonto_quotes.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="get", status=404, error="Quote not found"))
        from src.agent.tools.qonto_quotes import qonto_validate_quote

        result = await qonto_validate_quote("tenant-1", "nonexistent")

        assert result == {"error": "Quote not found"}
        assert mock_ws.send_command.call_count == 1


@pytest.mark.asyncio
async def test_list_quotes_sends_get():
    quotes_data = {"quotes": [{"id": "quote-abc"}], "meta": {"total_count": 1}}
    with patch("src.agent.tools.qonto_quotes.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=200, data=quotes_data))
        from src.agent.tools.qonto_quotes import qonto_list_quotes

        result = await qonto_list_quotes("tenant-1", status="draft")

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "GET"
        assert command.endpoint == "/quotes"
        assert command.query["status"] == "draft"
        assert command.query["per_page"] == "100"
        assert result == quotes_data


@pytest.mark.asyncio
async def test_get_quote_sends_get_with_id():
    with patch("src.agent.tools.qonto_quotes.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=200, data=QUOTE_RESPONSE))
        from src.agent.tools.qonto_quotes import qonto_get_quote

        result = await qonto_get_quote("tenant-1", "quote-abc")

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "GET"
        assert command.endpoint == "/quotes/quote-abc"
        assert result == QUOTE_RESPONSE


@pytest.mark.asyncio
async def test_create_quote_error_propagation():
    with patch("src.agent.tools.qonto_quotes.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=422, error="Invalid quote data"))
        from src.agent.tools.qonto_quotes import qonto_create_quote

        result = await qonto_create_quote("tenant-1", {})

        assert result == {"error": "Invalid quote data"}
