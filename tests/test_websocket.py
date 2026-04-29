"""Tests for WebSocket protocol, manager, and round-trip communication."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.websocket.protocol import WSCommand, WSResponse
from src.websocket.server import WSManager

# ---------------------------------------------------------------------------
# Protocol serialization tests
# ---------------------------------------------------------------------------


class TestWSCommandSerialization:
    def test_minimal_command(self):
        cmd = WSCommand(id="abc", method="GET", endpoint="/health")
        assert cmd.id == "abc"
        assert cmd.method == "GET"
        assert cmd.endpoint == "/health"
        assert cmd.body is None
        assert cmd.query is None

    def test_full_command(self):
        cmd = WSCommand(
            id="req-1",
            method="POST",
            endpoint="/quotes",
            body={"amount": 100},
            query={"page": 1},
        )
        assert cmd.body == {"amount": 100}
        assert cmd.query == {"page": 1}

    def test_command_json_round_trip(self):
        cmd = WSCommand(id="x", method="DELETE", endpoint="/items/5")
        json_str = cmd.model_dump_json()
        restored = WSCommand.model_validate_json(json_str)
        assert restored == cmd

    def test_command_with_body_json_round_trip(self):
        cmd = WSCommand(
            id="y",
            method="PATCH",
            endpoint="/clients/1",
            body={"name": "Acme"},
            query={"dry_run": "true"},
        )
        json_str = cmd.model_dump_json()
        restored = WSCommand.model_validate_json(json_str)
        assert restored == cmd


class TestWSResponseSerialization:
    def test_success_response(self):
        resp = WSResponse(id="abc", status=200, data={"ok": True})
        assert resp.id == "abc"
        assert resp.status == 200
        assert resp.data == {"ok": True}
        assert resp.error is None

    def test_error_response(self):
        resp = WSResponse(id="abc", status=503, error="Proxy not connected")
        assert resp.status == 503
        assert resp.error == "Proxy not connected"
        assert resp.data is None

    def test_response_json_round_trip(self):
        resp = WSResponse(id="r1", status=200, data={"list": [1, 2, 3]})
        json_str = resp.model_dump_json()
        restored = WSResponse.model_validate_json(json_str)
        assert restored == resp

    def test_error_response_json_round_trip(self):
        resp = WSResponse(id="r2", status=500, error="Something broke")
        json_str = resp.model_dump_json()
        restored = WSResponse.model_validate_json(json_str)
        assert restored == resp


# ---------------------------------------------------------------------------
# WSManager tests
# ---------------------------------------------------------------------------


class TestWSManager:
    def test_initial_state(self):
        manager = WSManager()
        assert manager.connections == {}

    @pytest.mark.asyncio
    async def test_connect_stores_websocket(self):
        manager = WSManager()
        mock_ws = AsyncMock()
        await manager.connect("tenant-1", mock_ws)
        assert "tenant-1" in manager.connections
        assert manager.connections["tenant-1"] is mock_ws
        mock_ws.accept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_replaces_existing(self):
        manager = WSManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect("tenant-1", ws1)
        await manager.connect("tenant-1", ws2)
        assert manager.connections["tenant-1"] is ws2

    def test_disconnect_removes_tenant(self):
        manager = WSManager()
        mock_ws = MagicMock()
        manager.connections["tenant-1"] = mock_ws
        manager.disconnect("tenant-1")
        assert "tenant-1" not in manager.connections

    def test_disconnect_missing_tenant_no_error(self):
        manager = WSManager()
        # Should not raise
        manager.disconnect("nonexistent-tenant")

    @pytest.mark.asyncio
    async def test_send_command_no_proxy_returns_503(self):
        manager = WSManager()
        cmd = WSCommand(id="req-1", method="GET", endpoint="/health")
        response = await manager.send_command("missing-tenant", cmd)
        assert response.status == 503
        assert response.id == "req-1"
        assert "not connected" in (response.error or "").lower()

    @pytest.mark.asyncio
    async def test_send_command_sends_and_receives(self):
        manager = WSManager()
        cmd = WSCommand(id="req-2", method="GET", endpoint="/quotes")
        expected_response = WSResponse(id="req-2", status=200, data={"quotes": []})

        mock_ws = AsyncMock()
        mock_ws.receive_text = AsyncMock(return_value=expected_response.model_dump_json())
        manager.connections["tenant-1"] = mock_ws

        response = await manager.send_command("tenant-1", cmd)

        mock_ws.send_text.assert_awaited_once_with(cmd.model_dump_json())
        assert response.status == 200
        assert response.id == "req-2"
        assert response.data == {"quotes": []}


# ---------------------------------------------------------------------------
# Protocol round-trip test (command -> serialise -> deserialise -> response)
# ---------------------------------------------------------------------------


class TestProtocolRoundTrip:
    def test_command_to_response_round_trip(self):
        """Simulate what happens over the wire: command is sent as JSON,
        proxy deserialises it, executes, returns WSResponse as JSON."""
        # Cloud side: create and serialise command
        original_cmd = WSCommand(
            id="rt-1",
            method="POST",
            endpoint="/invoices",
            body={"client_id": "c1", "amount": 500},
        )
        wire_cmd = original_cmd.model_dump_json()

        # Proxy side: deserialise, process
        received_cmd = WSCommand.model_validate_json(wire_cmd)
        assert received_cmd.id == "rt-1"
        assert received_cmd.body == {"client_id": "c1", "amount": 500}

        # Proxy side: build response and serialise
        proxy_response = WSResponse(id=received_cmd.id, status=201, data={"invoice_id": "inv-99"})
        wire_resp = proxy_response.model_dump_json()

        # Cloud side: deserialise response
        final_response = WSResponse.model_validate_json(wire_resp)
        assert final_response.id == "rt-1"
        assert final_response.status == 201
        assert final_response.data == {"invoice_id": "inv-99"}

    def test_error_round_trip(self):
        """Error response propagates cleanly over the wire."""
        cmd = WSCommand(id="rt-err", method="GET", endpoint="/nope")
        wire_cmd = cmd.model_dump_json()
        received_cmd = WSCommand.model_validate_json(wire_cmd)

        error_resp = WSResponse(id=received_cmd.id, status=404, error="Not found")
        wire_resp = error_resp.model_dump_json()

        final = WSResponse.model_validate_json(wire_resp)
        assert final.status == 404
        assert final.error == "Not found"
