"""Core resilience logic: failure tracking, extended downtime, subscription pausing."""

import uuid
from datetime import UTC, datetime

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.proxy import ProxyConnection
from src.models.subscription import Subscription


async def process_health_check_success(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Reset failure counter and update last check timestamp."""
    stmt = select(ProxyConnection).where(ProxyConnection.tenant_id == tenant_id)
    result = await session.execute(stmt)
    proxy = result.scalar_one_or_none()
    if proxy:
        proxy.consecutive_failures = 0
        proxy.last_health_check = datetime.now(UTC)
        await session.commit()


async def process_health_check_failure(session: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Increment failure counter. Returns action needed."""
    stmt = select(ProxyConnection).where(ProxyConnection.tenant_id == tenant_id)
    result = await session.execute(stmt)
    proxy = result.scalar_one_or_none()
    if not proxy:
        return {"action": "none"}

    proxy.consecutive_failures += 1
    proxy.last_health_check = datetime.now(UTC)
    await session.commit()

    if proxy.consecutive_failures == 3:
        return {"action": "notify_client", "tenant_id": str(tenant_id), "failures": 3}

    return {"action": "none", "failures": proxy.consecutive_failures}


async def check_extended_downtime(session: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Check if proxy has been down for 7+ days. If so, pause Stripe subscription."""
    stmt = select(ProxyConnection).where(ProxyConnection.tenant_id == tenant_id)
    result = await session.execute(stmt)
    proxy = result.scalar_one_or_none()
    if not proxy or not proxy.last_health_check:
        return {"action": "none"}

    last_check = proxy.last_health_check
    # SQLite returns naive datetimes; normalise to UTC-aware for comparison.
    if last_check.tzinfo is None:
        last_check = last_check.replace(tzinfo=UTC)
    days_since_check = (datetime.now(UTC) - last_check).days
    if days_since_check >= 7 and proxy.consecutive_failures >= 3:
        return {"action": "pause_subscription", "tenant_id": str(tenant_id)}

    return {"action": "none"}


async def pause_subscription(session: AsyncSession, tenant_id: uuid.UUID) -> bool:
    """Pause a tenant's Stripe subscription."""
    from src.config import settings

    stripe.api_key = settings.stripe_secret_key

    stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
    result = await session.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub or sub.status != "active":
        return False

    stripe.Subscription.modify(sub.stripe_subscription_id, pause_collection={"behavior": "void"})
    sub.status = "paused"
    await session.commit()
    return True


async def handle_cancellation(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Handle Stripe cancellation: mark for cleanup after 30 days."""
    stmt = select(ProxyConnection).where(ProxyConnection.tenant_id == tenant_id)
    result = await session.execute(stmt)
    proxy = result.scalar_one_or_none()
    if proxy:
        proxy.is_connected = False
        await session.commit()
    # Note: actual data deletion after 30 days would be handled by a scheduled task


async def notify_client_proxy_down(bot, telegram_user_id: int, failures: int) -> None:
    """Send Telegram notification about proxy being down."""
    await bot.send_message(
        chat_id=telegram_user_id,
        text=f"⚠️ Ton proxy Qonto ne repond plus ({failures} echecs consecutifs). "
        "Verifie que ton instance Railway est active.",
    )
