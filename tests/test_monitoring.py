"""Tests for monitoring resilience logic."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.proxy import ProxyConnection
from src.models.subscription import Subscription
from src.models.tenant import Tenant
from src.monitoring.resilience import (
    check_extended_downtime,
    handle_cancellation,
    notify_client_proxy_down,
    pause_subscription,
    process_health_check_failure,
    process_health_check_success,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_tenant(session: AsyncSession) -> Tenant:
    tenant = Tenant(name="Test Tenant")
    session.add(tenant)
    await session.flush()
    return tenant


async def _create_proxy(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    consecutive_failures: int = 0,
    last_health_check: datetime | None = None,
    is_connected: bool = True,
) -> ProxyConnection:
    proxy = ProxyConnection(
        tenant_id=tenant_id,
        shared_token="tok_test",
        consecutive_failures=consecutive_failures,
        last_health_check=last_health_check,
        is_connected=is_connected,
    )
    session.add(proxy)
    await session.commit()
    return proxy


async def _create_subscription(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    status: str = "active",
    stripe_subscription_id: str = "sub_test",
) -> Subscription:
    sub = Subscription(
        tenant_id=tenant_id,
        stripe_customer_id="cus_test",
        stripe_subscription_id=stripe_subscription_id,
        plan="solo",
        status=status,
        actions_used=0,
        actions_limit=50,
    )
    session.add(sub)
    await session.commit()
    return sub


# ---------------------------------------------------------------------------
# process_health_check_success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_success_resets_counter(db_session: AsyncSession) -> None:
    """process_health_check_success resets consecutive_failures to 0."""
    tenant = await _create_tenant(db_session)
    await _create_proxy(db_session, tenant.id, consecutive_failures=2)

    await process_health_check_success(db_session, tenant.id)

    from sqlalchemy import select

    result = await db_session.execute(select(ProxyConnection).where(ProxyConnection.tenant_id == tenant.id))
    proxy = result.scalar_one()
    assert proxy.consecutive_failures == 0
    assert proxy.last_health_check is not None


# ---------------------------------------------------------------------------
# process_health_check_failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_failure_increments_counter(db_session: AsyncSession) -> None:
    """process_health_check_failure increments consecutive_failures by 1."""
    tenant = await _create_tenant(db_session)
    await _create_proxy(db_session, tenant.id, consecutive_failures=0)

    result = await process_health_check_failure(db_session, tenant.id)

    from sqlalchemy import select

    row = await db_session.execute(select(ProxyConnection).where(ProxyConnection.tenant_id == tenant.id))
    proxy = row.scalar_one()
    assert proxy.consecutive_failures == 1
    assert result["action"] == "none"
    assert result["failures"] == 1


@pytest.mark.asyncio
async def test_three_failures_triggers_notify(db_session: AsyncSession) -> None:
    """process_health_check_failure with 2 existing failures returns notify_client action."""
    tenant = await _create_tenant(db_session)
    await _create_proxy(db_session, tenant.id, consecutive_failures=2)

    result = await process_health_check_failure(db_session, tenant.id)

    assert result["action"] == "notify_client"
    assert result["failures"] == 3
    assert result["tenant_id"] == str(tenant.id)


@pytest.mark.asyncio
async def test_health_failure_no_proxy_returns_none(db_session: AsyncSession) -> None:
    """process_health_check_failure returns action=none when no proxy exists."""
    random_tenant_id = uuid.uuid4()
    result = await process_health_check_failure(db_session, random_tenant_id)
    assert result["action"] == "none"


# ---------------------------------------------------------------------------
# check_extended_downtime
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extended_downtime_triggers_pause(db_session: AsyncSession) -> None:
    """check_extended_downtime returns pause_subscription when down 8 days with 3+ failures."""
    tenant = await _create_tenant(db_session)
    eight_days_ago = datetime.now(UTC) - timedelta(days=8)
    await _create_proxy(db_session, tenant.id, consecutive_failures=3, last_health_check=eight_days_ago)

    result = await check_extended_downtime(db_session, tenant.id)

    assert result["action"] == "pause_subscription"
    assert result["tenant_id"] == str(tenant.id)


@pytest.mark.asyncio
async def test_not_extended_if_recent(db_session: AsyncSession) -> None:
    """check_extended_downtime returns action=none when last check was recent."""
    tenant = await _create_tenant(db_session)
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    await _create_proxy(db_session, tenant.id, consecutive_failures=5, last_health_check=one_hour_ago)

    result = await check_extended_downtime(db_session, tenant.id)

    assert result["action"] == "none"


@pytest.mark.asyncio
async def test_not_extended_if_failures_below_threshold(db_session: AsyncSession) -> None:
    """check_extended_downtime returns action=none when failures < 3 even if old check."""
    tenant = await _create_tenant(db_session)
    ten_days_ago = datetime.now(UTC) - timedelta(days=10)
    await _create_proxy(db_session, tenant.id, consecutive_failures=1, last_health_check=ten_days_ago)

    result = await check_extended_downtime(db_session, tenant.id)

    assert result["action"] == "none"


@pytest.mark.asyncio
async def test_not_extended_if_no_health_check(db_session: AsyncSession) -> None:
    """check_extended_downtime returns action=none when last_health_check is None."""
    tenant = await _create_tenant(db_session)
    await _create_proxy(db_session, tenant.id, consecutive_failures=5, last_health_check=None)

    result = await check_extended_downtime(db_session, tenant.id)

    assert result["action"] == "none"


# ---------------------------------------------------------------------------
# pause_subscription
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pause_subscription_updates_status(db_session: AsyncSession) -> None:
    """pause_subscription calls Stripe and sets subscription status to paused."""
    tenant = await _create_tenant(db_session)
    await _create_subscription(db_session, tenant.id, status="active", stripe_subscription_id="sub_abc")

    with patch("src.monitoring.resilience.stripe") as mock_stripe:
        mock_stripe.Subscription.modify = MagicMock()
        success = await pause_subscription(db_session, tenant.id)

    assert success is True
    mock_stripe.Subscription.modify.assert_called_once_with("sub_abc", pause_collection={"behavior": "void"})

    from sqlalchemy import select

    result = await db_session.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    sub = result.scalar_one()
    assert sub.status == "paused"


@pytest.mark.asyncio
async def test_pause_subscription_skips_if_already_paused(db_session: AsyncSession) -> None:
    """pause_subscription returns False when subscription is not active."""
    tenant = await _create_tenant(db_session)
    await _create_subscription(db_session, tenant.id, status="paused")

    with patch("src.monitoring.resilience.stripe") as mock_stripe:
        success = await pause_subscription(db_session, tenant.id)

    assert success is False
    mock_stripe.Subscription.modify.assert_not_called()


@pytest.mark.asyncio
async def test_pause_subscription_no_subscription(db_session: AsyncSession) -> None:
    """pause_subscription returns False when no subscription exists."""
    random_tenant_id = uuid.uuid4()

    with patch("src.monitoring.resilience.stripe"):
        success = await pause_subscription(db_session, random_tenant_id)

    assert success is False


# ---------------------------------------------------------------------------
# handle_cancellation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_cancellation_disconnects_proxy(db_session: AsyncSession) -> None:
    """handle_cancellation sets is_connected=False on the proxy."""
    tenant = await _create_tenant(db_session)
    await _create_proxy(db_session, tenant.id, is_connected=True)

    await handle_cancellation(db_session, tenant.id)

    from sqlalchemy import select

    result = await db_session.execute(select(ProxyConnection).where(ProxyConnection.tenant_id == tenant.id))
    proxy = result.scalar_one()
    assert proxy.is_connected is False


@pytest.mark.asyncio
async def test_handle_cancellation_no_proxy(db_session: AsyncSession) -> None:
    """handle_cancellation is a no-op when no proxy exists."""
    random_tenant_id = uuid.uuid4()
    # Should not raise
    await handle_cancellation(db_session, random_tenant_id)


# ---------------------------------------------------------------------------
# notify_client_proxy_down
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notify_client_proxy_down_sends_message() -> None:
    """notify_client_proxy_down calls bot.send_message with correct args."""
    mock_bot = AsyncMock()
    await notify_client_proxy_down(mock_bot, telegram_user_id=12345, failures=3)

    mock_bot.send_message.assert_called_once()
    call_kwargs = mock_bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 12345
    assert "3" in call_kwargs["text"]
