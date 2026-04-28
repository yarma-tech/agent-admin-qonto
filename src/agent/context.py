import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import ConversationMessage
from src.rag.search import search_memory


async def build_context(session: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Return the last 10 ConversationMessages for a tenant in chronological order.

    If the most recent message is from the user, top-5 RAG results are prepended
    as a system message so the agent has relevant business context.
    """
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.tenant_id == tenant_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(10)
    )
    messages = result.scalars().all()
    # Reverse so the oldest of the 10 comes first (chronological order)
    messages = list(reversed(messages))
    chat_messages: list[dict] = [{"role": m.role, "content": m.content} for m in messages]

    # Inject RAG context when there is at least one user message to query against.
    last_user_content: str | None = None
    for msg in reversed(chat_messages):
        if msg["role"] == "user":
            last_user_content = msg["content"]
            break

    if last_user_content:
        try:
            rag_results = await search_memory(session, tenant_id, last_user_content, limit=5)
            if rag_results:
                rag_text = "\n".join(f"- {r}" for r in rag_results)
                system_msg = {
                    "role": "system",
                    "content": f"Contexte mémoire pertinent:\n{rag_text}",
                }
                chat_messages = [system_msg] + chat_messages
        except Exception:
            # RAG is best-effort — never break the agent loop
            pass

    return chat_messages
