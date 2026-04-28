import uuid

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.context import build_context
from src.agent.router import select_model
from src.config import settings
from src.models.conversation import ConversationMessage


async def run_agent(session: AsyncSession, tenant_id: uuid.UUID, user_message: str) -> str:
    history = await build_context(session, tenant_id)
    model = select_model(user_message)

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    messages = history + [{"role": "user", "content": user_message}]

    # Simple messages.create — tool loop will be added when tools are implemented
    response = await client.messages.create(
        model=model,
        max_tokens=1024,
        system=(
            "Tu es un assistant Qonto pour freelances français. Tu aides à gérer devis, factures et memos business. "
            "Réponds en français. Sois concis et professionnel."
        ),
        messages=messages,
    )

    assistant_text = response.content[0].text

    # Save both messages to conversation history
    session.add(ConversationMessage(tenant_id=tenant_id, role="user", content=user_message))
    session.add(ConversationMessage(tenant_id=tenant_id, role="assistant", content=assistant_text))
    await session.commit()

    return assistant_text
