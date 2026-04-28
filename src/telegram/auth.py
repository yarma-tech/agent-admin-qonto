from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tenant import Tenant, User


async def get_or_create_tenant(
    session: AsyncSession,
    telegram_user_id: int,
    first_name: str,
) -> tuple[Tenant, User]:
    """Look up a User by telegram_user_id.

    If found, return the existing tenant and user.
    If not, create a new Tenant and User, commit, and return them.
    """
    result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
    user = result.scalar_one_or_none()

    if user is not None:
        result_tenant = await session.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result_tenant.scalar_one()
        return tenant, user

    tenant = Tenant(name=first_name)
    session.add(tenant)
    await session.flush()  # get tenant.id before creating user

    user = User(
        telegram_user_id=telegram_user_id,
        first_name=first_name,
        tenant_id=tenant.id,
    )
    session.add(user)
    await session.commit()

    return tenant, user
