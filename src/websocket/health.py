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
                    await _handle_success(tenant_id)
                else:
                    await _handle_failure(tenant_id)
            except Exception:
                await _handle_failure(tenant_id)


async def _handle_success(tenant_id: str) -> None:
    """Handle a successful health check: reset failures, check extended downtime."""
    from src.db import get_db
    from src.monitoring.resilience import process_health_check_success

    async for session in get_db():
        await process_health_check_success(session, uuid.UUID(tenant_id))
        break


async def _handle_failure(tenant_id: str) -> None:
    """Handle a failed health check: increment failures, notify if threshold reached, check extended downtime."""
    from src.db import get_db
    from src.monitoring.resilience import (
        check_extended_downtime,
        pause_subscription,
        process_health_check_failure,
    )

    async for session in get_db():
        result = await process_health_check_failure(session, uuid.UUID(tenant_id))

        if result.get("action") == "notify_client":
            await _send_telegram_notification(tenant_id, result.get("failures", 3))

        downtime = await check_extended_downtime(session, uuid.UUID(tenant_id))
        if downtime.get("action") == "pause_subscription":
            await pause_subscription(session, uuid.UUID(tenant_id))

        break


async def _send_telegram_notification(tenant_id: str, failures: int) -> None:
    """Look up the tenant's Telegram user ID and send a notification."""
    try:
        from sqlalchemy import select

        from src.db import get_db
        from src.models.tenant import User
        from src.monitoring.resilience import notify_client_proxy_down
        from src.telegram.bot import bot

        async for session in get_db():
            result = await session.execute(select(User).where(User.tenant_id == uuid.UUID(tenant_id)))
            user = result.scalar_one_or_none()
            if user:
                await notify_client_proxy_down(bot, user.telegram_user_id, failures)
            break
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Legacy helpers kept for backward compatibility (used by older code paths)
# ---------------------------------------------------------------------------


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
