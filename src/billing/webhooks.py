import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.subscription import Subscription
from src.models.tenant import Tenant, User

PLAN_LIMITS = {
    "solo": 50,
    "pro": -1,  # unlimited
}


async def handle_stripe_webhook(payload: bytes, sig_header: str, session: AsyncSession) -> None:
    """Verify Stripe webhook signature and dispatch to event handlers."""
    event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)

    if event.type == "checkout.session.completed":
        await _handle_checkout_completed(event.data.object, session)
    elif event.type == "customer.subscription.deleted":
        await _handle_subscription_deleted(event.data.object, session)
    elif event.type == "customer.subscription.updated":
        await _handle_subscription_updated(event.data.object, session)


async def _handle_checkout_completed(checkout_session: dict, session: AsyncSession) -> None:
    """Create a Subscription record after successful checkout."""
    metadata = checkout_session.get("metadata", {})
    telegram_user_id = int(metadata.get("telegram_user_id", 0))
    plan = metadata.get("plan", "solo")

    # Find user by telegram_user_id
    result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return

    # Find tenant
    tenant_result = await session.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        return

    # Check if subscription already exists for this tenant
    existing_result = await session.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    existing = existing_result.scalar_one_or_none()

    stripe_customer_id = checkout_session.get("customer", "") or ""
    stripe_subscription_id = checkout_session.get("subscription", "") or ""
    actions_limit = PLAN_LIMITS.get(plan, 50)

    if existing is not None:
        # Update existing subscription
        existing.stripe_customer_id = stripe_customer_id
        existing.stripe_subscription_id = stripe_subscription_id
        existing.plan = plan
        existing.status = "active"
        existing.actions_limit = actions_limit
    else:
        subscription = Subscription(
            tenant_id=tenant.id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            plan=plan,
            status="active",
            actions_used=0,
            actions_limit=actions_limit,
        )
        session.add(subscription)

    await session.commit()


async def _handle_subscription_deleted(stripe_sub: dict, session: AsyncSession) -> None:
    """Mark subscription as canceled."""
    stripe_subscription_id = stripe_sub.get("id", "")

    result = await session.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if subscription is not None:
        subscription.status = "canceled"
        await session.commit()


async def _handle_subscription_updated(stripe_sub: dict, session: AsyncSession) -> None:
    """Update plan and status on subscription update."""
    stripe_subscription_id = stripe_sub.get("id", "")
    new_status = stripe_sub.get("status", "active")

    result = await session.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        return

    # Map Stripe statuses to our statuses
    status_map = {
        "active": "active",
        "paused": "paused",
        "canceled": "canceled",
        "past_due": "paused",
        "unpaid": "paused",
    }
    subscription.status = status_map.get(new_status, new_status)
    await session.commit()
