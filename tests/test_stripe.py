"""Tests for Stripe billing: checkout, webhooks, and usage tracking."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.billing.stripe_checkout import create_checkout_session
from src.billing.usage import check_can_act, get_usage, increment_usage
from src.billing.webhooks import handle_stripe_webhook
from src.models.subscription import Subscription
from src.models.tenant import Tenant, User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_tenant_and_user(session: AsyncSession, telegram_user_id: int = 123456):
    """Create and persist a Tenant + User, returning (tenant, user)."""
    tenant = Tenant(name="Test Tenant")
    session.add(tenant)
    await session.flush()

    user = User(
        telegram_user_id=telegram_user_id,
        first_name="Alice",
        tenant_id=tenant.id,
    )
    session.add(user)
    await session.commit()
    return tenant, user


async def _create_subscription(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    plan: str = "solo",
    actions_used: int = 0,
    actions_limit: int = 50,
    stripe_subscription_id: str = "sub_test123",
):
    sub = Subscription(
        tenant_id=tenant_id,
        stripe_customer_id="cus_test123",
        stripe_subscription_id=stripe_subscription_id,
        plan=plan,
        status="active",
        actions_used=actions_used,
        actions_limit=actions_limit,
    )
    session.add(sub)
    await session.commit()
    return sub


# ---------------------------------------------------------------------------
# create_checkout_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_checkout_session_returns_url():
    """create_checkout_session should return the Stripe session URL."""
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_abc123"

    with patch("src.billing.stripe_checkout.stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        url = await create_checkout_session(telegram_user_id=42, plan="solo")

    assert url == "https://checkout.stripe.com/pay/cs_test_abc123"
    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["metadata"]["telegram_user_id"] == "42"
    assert call_kwargs["metadata"]["plan"] == "solo"
    assert call_kwargs["mode"] == "subscription"


@pytest.mark.asyncio
async def test_create_checkout_session_pro_plan():
    """create_checkout_session passes plan=pro in metadata."""
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/pay/cs_pro"

    with patch("src.billing.stripe_checkout.stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        url = await create_checkout_session(telegram_user_id=99, plan="pro")

    assert url == "https://checkout.stripe.com/pay/cs_pro"
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["metadata"]["plan"] == "pro"


# ---------------------------------------------------------------------------
# handle_stripe_webhook — checkout.session.completed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webhook_checkout_completed_creates_subscription(db_session: AsyncSession):
    """checkout.session.completed should create a Subscription record."""
    tenant, user = await _create_tenant_and_user(db_session, telegram_user_id=111)

    fake_event = MagicMock()
    fake_event.type = "checkout.session.completed"
    fake_event.data.object = {
        "metadata": {"telegram_user_id": "111", "plan": "solo"},
        "customer": "cus_abc",
        "subscription": "sub_abc",
    }

    with patch("src.billing.webhooks.stripe.Webhook.construct_event", return_value=fake_event):
        await handle_stripe_webhook(b"payload", "sig_header", db_session)

    # Verify subscription was created
    from sqlalchemy import select

    result = await db_session.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    sub = result.scalar_one_or_none()
    assert sub is not None
    assert sub.plan == "solo"
    assert sub.status == "active"
    assert sub.stripe_customer_id == "cus_abc"
    assert sub.stripe_subscription_id == "sub_abc"
    assert sub.actions_limit == 50


@pytest.mark.asyncio
async def test_webhook_checkout_completed_pro_plan(db_session: AsyncSession):
    """checkout.session.completed with plan=pro sets actions_limit=-1."""
    tenant, user = await _create_tenant_and_user(db_session, telegram_user_id=222)

    fake_event = MagicMock()
    fake_event.type = "checkout.session.completed"
    fake_event.data.object = {
        "metadata": {"telegram_user_id": "222", "plan": "pro"},
        "customer": "cus_pro",
        "subscription": "sub_pro",
    }

    with patch("src.billing.webhooks.stripe.Webhook.construct_event", return_value=fake_event):
        await handle_stripe_webhook(b"payload", "sig_header", db_session)

    from sqlalchemy import select

    result = await db_session.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    sub = result.scalar_one_or_none()
    assert sub is not None
    assert sub.plan == "pro"
    assert sub.actions_limit == -1


# ---------------------------------------------------------------------------
# handle_stripe_webhook — customer.subscription.deleted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webhook_subscription_deleted_cancels(db_session: AsyncSession):
    """customer.subscription.deleted should set status='canceled'."""
    tenant, _ = await _create_tenant_and_user(db_session, telegram_user_id=333)
    await _create_subscription(db_session, tenant.id, stripe_subscription_id="sub_del")

    fake_event = MagicMock()
    fake_event.type = "customer.subscription.deleted"
    fake_event.data.object = {"id": "sub_del"}

    with patch("src.billing.webhooks.stripe.Webhook.construct_event", return_value=fake_event):
        await handle_stripe_webhook(b"payload", "sig_header", db_session)

    from sqlalchemy import select

    result = await db_session.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    sub = result.scalar_one_or_none()
    assert sub.status == "canceled"


# ---------------------------------------------------------------------------
# handle_stripe_webhook — customer.subscription.updated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webhook_subscription_updated_status(db_session: AsyncSession):
    """customer.subscription.updated should update the subscription status."""
    tenant, _ = await _create_tenant_and_user(db_session, telegram_user_id=444)
    await _create_subscription(db_session, tenant.id, stripe_subscription_id="sub_upd")

    fake_event = MagicMock()
    fake_event.type = "customer.subscription.updated"
    fake_event.data.object = {"id": "sub_upd", "status": "past_due"}

    with patch("src.billing.webhooks.stripe.Webhook.construct_event", return_value=fake_event):
        await handle_stripe_webhook(b"payload", "sig_header", db_session)

    from sqlalchemy import select

    result = await db_session.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    sub = result.scalar_one_or_none()
    assert sub.status == "paused"


# ---------------------------------------------------------------------------
# increment_usage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_increment_usage_increments(db_session: AsyncSession):
    """increment_usage should increment actions_used by 1."""
    tenant, _ = await _create_tenant_and_user(db_session, telegram_user_id=555)
    await _create_subscription(db_session, tenant.id, actions_used=5, actions_limit=50)

    used, limit = await increment_usage(db_session, tenant.id)

    assert used == 6
    assert limit == 50


@pytest.mark.asyncio
async def test_increment_usage_no_subscription(db_session: AsyncSession):
    """increment_usage returns (0, 0) when no subscription exists."""
    random_tenant_id = uuid.uuid4()
    used, limit = await increment_usage(db_session, random_tenant_id)
    assert used == 0
    assert limit == 0


# ---------------------------------------------------------------------------
# check_can_act
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_can_act_under_limit(db_session: AsyncSession):
    """check_can_act returns True when actions_used < actions_limit."""
    tenant, _ = await _create_tenant_and_user(db_session, telegram_user_id=666)
    await _create_subscription(db_session, tenant.id, actions_used=10, actions_limit=50)

    can_act = await check_can_act(db_session, tenant.id)
    assert can_act is True


@pytest.mark.asyncio
async def test_check_can_act_at_limit(db_session: AsyncSession):
    """check_can_act returns False when actions_used >= actions_limit."""
    tenant, _ = await _create_tenant_and_user(db_session, telegram_user_id=777)
    await _create_subscription(db_session, tenant.id, actions_used=50, actions_limit=50)

    can_act = await check_can_act(db_session, tenant.id)
    assert can_act is False


@pytest.mark.asyncio
async def test_check_can_act_pro_plan_unlimited(db_session: AsyncSession):
    """check_can_act returns True for pro plan (actions_limit=-1) regardless of usage."""
    tenant, _ = await _create_tenant_and_user(db_session, telegram_user_id=888)
    await _create_subscription(db_session, tenant.id, plan="pro", actions_used=999, actions_limit=-1)

    can_act = await check_can_act(db_session, tenant.id)
    assert can_act is True


@pytest.mark.asyncio
async def test_check_can_act_no_subscription(db_session: AsyncSession):
    """check_can_act returns False when no subscription exists."""
    random_tenant_id = uuid.uuid4()
    can_act = await check_can_act(db_session, random_tenant_id)
    assert can_act is False


# ---------------------------------------------------------------------------
# get_usage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_usage_returns_correct_data(db_session: AsyncSession):
    """get_usage returns the correct usage dict."""
    tenant, _ = await _create_tenant_and_user(db_session, telegram_user_id=999)
    await _create_subscription(db_session, tenant.id, plan="solo", actions_used=12, actions_limit=50)

    usage = await get_usage(db_session, tenant.id)

    assert usage == {"actions_used": 12, "actions_limit": 50, "plan": "solo"}


@pytest.mark.asyncio
async def test_get_usage_no_subscription(db_session: AsyncSession):
    """get_usage returns zero-values when no subscription exists."""
    random_tenant_id = uuid.uuid4()
    usage = await get_usage(db_session, random_tenant_id)
    assert usage == {"actions_used": 0, "actions_limit": 0, "plan": "none"}
