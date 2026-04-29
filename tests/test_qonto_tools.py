"""Tests for Qonto client and product agent tools."""

from unittest.mock import AsyncMock, patch

import pytest

from src.websocket.protocol import WSResponse


@pytest.mark.asyncio
async def test_client_find_sends_correct_command():
    with patch("src.agent.tools.qonto_clients.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(
            return_value=WSResponse(id="test", status=200, data={"clients": [{"name": "ACME"}]})
        )
        from src.agent.tools.qonto_clients import qonto_client_find

        result = await qonto_client_find("tenant-1", "ACME")

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "GET"
        assert command.endpoint == "/clients"
        assert command.query == {"search": "ACME"}
        assert result == {"clients": [{"name": "ACME"}]}


@pytest.mark.asyncio
async def test_client_create_sends_post():
    with patch("src.agent.tools.qonto_clients.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=200, data={"id": "new-client-id"}))
        from src.agent.tools.qonto_clients import qonto_client_create

        result = await qonto_client_create("tenant-1", {"name": "New Corp", "kind": "company"})

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "POST"
        assert command.endpoint == "/clients"
        assert command.body == {"name": "New Corp", "kind": "company"}
        assert result == {"id": "new-client-id"}


@pytest.mark.asyncio
async def test_client_find_returns_error_on_proxy_failure():
    with patch("src.agent.tools.qonto_clients.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=503, error="Proxy not connected"))
        from src.agent.tools.qonto_clients import qonto_client_find

        result = await qonto_client_find("tenant-1", "ACME")
        assert result == {"error": "Proxy not connected"}


@pytest.mark.asyncio
async def test_client_create_returns_error_on_proxy_failure():
    with patch("src.agent.tools.qonto_clients.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=503, error="Proxy not connected"))
        from src.agent.tools.qonto_clients import qonto_client_create

        result = await qonto_client_create("tenant-1", {"name": "Fail Corp"})
        assert result == {"error": "Proxy not connected"}


@pytest.mark.asyncio
async def test_product_find_sends_correct_command():
    with patch("src.agent.tools.qonto_products.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(
            return_value=WSResponse(id="test", status=200, data={"products": [{"name": "Widget"}]})
        )
        from src.agent.tools.qonto_products import qonto_product_find

        result = await qonto_product_find("tenant-1", "Widget")

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "GET"
        assert command.endpoint == "/products"
        assert command.query == {"search": "Widget"}
        assert result == {"products": [{"name": "Widget"}]}


@pytest.mark.asyncio
async def test_product_find_returns_error_on_proxy_failure():
    with patch("src.agent.tools.qonto_products.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=503, error="Proxy not connected"))
        from src.agent.tools.qonto_products import qonto_product_find

        result = await qonto_product_find("tenant-1", "Widget")
        assert result == {"error": "Proxy not connected"}


@pytest.mark.asyncio
async def test_product_create_sends_post():
    with patch("src.agent.tools.qonto_products.ws_manager") as mock_ws:
        mock_ws.send_command = AsyncMock(return_value=WSResponse(id="test", status=200, data={"id": "new-product-id"}))
        from src.agent.tools.qonto_products import qonto_product_create

        result = await qonto_product_create("tenant-1", {"name": "Widget Pro", "unit_price": 4900})

        command = mock_ws.send_command.call_args[0][1]
        assert command.method == "POST"
        assert command.endpoint == "/products"
        assert command.body == {"name": "Widget Pro", "unit_price": 4900}
        assert result == {"id": "new-product-id"}
