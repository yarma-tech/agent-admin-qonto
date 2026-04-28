import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import Subscription


async def increment_usage(session: AsyncSession, tenant_id: uuid.UUID) -> tuple[int, int]:
    """Increment actions_used for tenant's subscription.

    Returns (actions_used, actions_limit).
    """
    result = await session.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
    subscription = result.scalar_one_or_none()
    if subscription is None:
        return (0, 0)

    subscription.actions_used += 1
    await session.commit()
    return (subscription.actions_used, subscription.actions_limit)


async def get_usage(session: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Return usage info for the tenant's subscription."""
    result = await session.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
    subscription = result.scalar_one_or_none()
    if subscription is None:
        return {"actions_used": 0, "actions_limit": 0, "plan": "none"}

    return {
        "actions_used": subscription.actions_used,
        "actions_limit": subscription.actions_limit,
        "plan": subscription.plan,
    }


async def check_can_act(session: AsyncSession, tenant_id: uuid.UUID) -> bool:
    """Return True if the tenant is under their action limit (or on pro plan)."""
    result = await session.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
    subscription = result.scalar_one_or_none()
    if subscription is None:
        return False

    # Pro plan (-1 limit) means unlimited
    if subscription.actions_limit == -1:
        return True

    return subscription.actions_used < subscription.actions_limit
