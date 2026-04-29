"""WebSocket client running on the Railway proxy side.

Connects to the central backend, receives WSCommand messages, executes them
against the Qonto API via api_fetch, and sends back WSResponse messages.
"""

import asyncio
from typing import Any

import websockets
from pydantic import BaseModel

from src.config import settings
from src.qonto_client import api_fetch


# ---------------------------------------------------------------------------
# Protocol models (mirror of src/websocket/protocol.py in the cloud backend)
# ---------------------------------------------------------------------------


class WSCommand(BaseModel):
    id: str  # Request ID for correlation
    method: str  # GET, POST, PATCH, PUT, DELETE
    endpoint: str  # e.g. /quotes
    body: dict | None = None
    query: dict | None = None


class WSResponse(BaseModel):
    id: str
    status: int
    data: Any = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Command execution and connection loop
# ---------------------------------------------------------------------------


async def execute_command(command: WSCommand) -> WSResponse:
    """Execute a command by forwarding it to the Qonto API."""
    try:
        result = await api_fetch(
            command.method,
            command.endpoint,
            body=command.body,
            query=command.query,
        )
        return WSResponse(id=command.id, status=200, data=result)
    except Exception as e:
        return WSResponse(id=command.id, status=500, error=str(e))


async def ws_connect() -> None:
    """Connect to the central backend WebSocket with exponential backoff retry."""
    url = f"{settings.central_ws_url}?token={settings.shared_token}"
    backoff = 1
    while True:
        try:
            async with websockets.connect(url) as ws:
                backoff = 1  # Reset on successful connection
                async for message in ws:
                    command = WSCommand.model_validate_json(message)
                    response = await execute_command(command)
                    await ws.send(response.model_dump_json())
        except Exception:
            await asyncio.sleep(min(backoff, 60))
            backoff *= 2
