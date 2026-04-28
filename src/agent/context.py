import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import ConversationMessage


async def build_context(session: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Return the last 10 ConversationMessages for a tenant in chronological order."""
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.tenant_id == tenant_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(10)
    )
    messages = result.scalars().all()
    # Reverse so the oldest of the 10 comes first (chronological order)
    messages = list(reversed(messages))
    return [{"role": m.role, "content": m.content} for m in messages]
