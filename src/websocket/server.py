"""WebSocket server manager for the central backend."""

from fastapi import WebSocket, WebSocketDisconnect

from src.websocket.protocol import WSCommand, WSResponse


class WSManager:
    def __init__(self) -> None:
        self.connections: dict[str, WebSocket] = {}  # tenant_id -> websocket

    async def connect(self, tenant_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[tenant_id] = websocket

    def disconnect(self, tenant_id: str) -> None:
        self.connections.pop(tenant_id, None)

    async def send_command(self, tenant_id: str, command: WSCommand) -> WSResponse:
        ws = self.connections.get(tenant_id)
        if not ws:
            return WSResponse(id=command.id, status=503, error="Proxy not connected")
        await ws.send_text(command.model_dump_json())
        response_text = await ws.receive_text()
        return WSResponse.model_validate_json(response_text)


ws_manager = WSManager()


def valid_token(token: str | None, tenant_id: str) -> bool:
    """Validate the shared token against the DB record for this tenant."""
    # Import here to avoid circular imports at module load time
    # Actual validation is deferred to the endpoint which has DB access
    return token is not None and len(token) > 0


async def websocket_endpoint(websocket: WebSocket, tenant_id: str) -> None:
    """FastAPI WebSocket endpoint handler — to be registered in main.py."""
    import uuid as _uuid

    from sqlalchemy import select

    from src.db import get_db
    from src.models.proxy import ProxyConnection

    token = websocket.query_params.get("token")

    # Validate token against DB
    token_valid = False
    async for session in get_db():
        result = await session.execute(
            select(ProxyConnection).where(ProxyConnection.tenant_id == _uuid.UUID(tenant_id))
        )
        proxy_conn = result.scalar_one_or_none()
        if proxy_conn and proxy_conn.shared_token == token:
            token_valid = True
        break

    if not token_valid:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(tenant_id, websocket)

    # Mark as connected
    async for session in get_db():
        result = await session.execute(
            select(ProxyConnection).where(ProxyConnection.tenant_id == _uuid.UUID(tenant_id))
        )
        proxy_conn = result.scalar_one_or_none()
        if proxy_conn:
            proxy_conn.is_connected = True
            await session.commit()
        break

    try:
        while True:
            await websocket.receive_text()  # Keep alive / handle pings
    except WebSocketDisconnect:
        ws_manager.disconnect(tenant_id)
        # Mark as disconnected
        async for session in get_db():
            result = await session.execute(
                select(ProxyConnection).where(ProxyConnection.tenant_id == _uuid.UUID(tenant_id))
            )
            proxy_conn = result.scalar_one_or_none()
            if proxy_conn:
                proxy_conn.is_connected = False
                await session.commit()
            break
