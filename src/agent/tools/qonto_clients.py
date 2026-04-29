"""Agent tools for Qonto client management via WebSocket proxy."""

import uuid

from src.websocket.protocol import WSCommand
from src.websocket.server import ws_manager


async def qonto_client_find(tenant_id: str, name: str) -> dict:
    """Search Qonto clients by name."""
    command = WSCommand(
        id=str(uuid.uuid4()),
        method="GET",
        endpoint="/clients",
        query={"search": name},
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_client_create(tenant_id: str, client_data: dict) -> dict:
    """Create a new Qonto client. Requires confirmation from user."""
    command = WSCommand(
        id=str(uuid.uuid4()),
        method="POST",
        endpoint="/clients",
        body=client_data,
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data
