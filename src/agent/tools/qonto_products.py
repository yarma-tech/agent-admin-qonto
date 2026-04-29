"""Agent tools for Qonto product/article management via WebSocket proxy."""

import uuid

from src.websocket.protocol import WSCommand
from src.websocket.server import ws_manager


async def qonto_product_find(tenant_id: str, name: str) -> dict:
    """Search Qonto products/articles by name."""
    command = WSCommand(
        id=str(uuid.uuid4()),
        method="GET",
        endpoint="/products",
        query={"search": name},
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data


async def qonto_product_create(tenant_id: str, product_data: dict) -> dict:
    """Create a new Qonto product/article. Requires confirmation from user."""
    command = WSCommand(
        id=str(uuid.uuid4()),
        method="POST",
        endpoint="/products",
        body=product_data,
    )
    response = await ws_manager.send_command(tenant_id, command)
    if response.error:
        return {"error": response.error}
    return response.data
