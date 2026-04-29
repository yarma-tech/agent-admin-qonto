"""Health check scheduler for proxy connections."""

import asyncio
import uuid

from src.websocket.protocol import WSCommand
from src.websocket.server import ws_manager

HEALTH_CHECK_INTERVAL = 6 * 60 * 60  # 6 hours in seconds


async def health_check_loop() -> None:
    """Periodically ping all connected proxies and update failure counters."""
    while True:
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        for tenant_id in list(ws_manager.connections.keys()):
            try:
                command = WSCommand(id="health", method="GET", endpoint="/health")
                response = await asyncio.wait_for(ws_manager.send_command(tenant_id, command), timeout=30)
                if response.status == 200:
                    await _reset_failures(tenant_id)
                else:
                    await _increment_failures(tenant_id)
            except Exception:
                await _increment_failures(tenant_id)


async def _reset_failures(tenant_id: str) -> None:
    """Reset the consecutive_failures counter for a tenant proxy."""
    from sqlalchemy import select

    from src.db import get_db
    from src.models.proxy import ProxyConnection

    async for session in get_db():
        result = await session.execute(select(ProxyConnection).where(ProxyConnection.tenant_id == uuid.UUID(tenant_id)))
        proxy_conn = result.scalar_one_or_none()
        if proxy_conn:
            proxy_conn.consecutive_failures = 0
            from datetime import UTC, datetime

            proxy_conn.last_health_check = datetime.now(UTC)
            await session.commit()
        break


async def _increment_failures(tenant_id: str) -> None:
    """Increment the consecutive_failures counter for a tenant proxy."""
    from sqlalchemy import select

    from src.db import get_db
    from src.models.proxy import ProxyConnection

    async for session in get_db():
        result = await session.execute(select(ProxyConnection).where(ProxyConnection.tenant_id == uuid.UUID(tenant_id)))
        proxy_conn = result.scalar_one_or_none()
        if proxy_conn:
            proxy_conn.consecutive_failures = (proxy_conn.consecutive_failures or 0) + 1
            from datetime import UTC, datetime

            proxy_conn.last_health_check = datetime.now(UTC)
            await session.commit()
        break
