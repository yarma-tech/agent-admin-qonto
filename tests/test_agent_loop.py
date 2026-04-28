import uuid

import pytest

from src.agent.context import build_context
from src.models.conversation import ConversationMessage


@pytest.mark.asyncio
async def test_build_context_returns_last_10(db_session):
    tenant_id = uuid.uuid4()

    # Create 15 messages
    for i in range(15):
        db_session.add(
            ConversationMessage(
                tenant_id=tenant_id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"message {i}",
            )
        )
    await db_session.commit()

    result = await build_context(db_session, tenant_id)

    assert len(result) == 10
    # Messages should be in chronological order (oldest first)
    # The last 10 messages are indices 5..14
    assert result[0]["content"] == "message 5"
    assert result[-1]["content"] == "message 14"
    # Each entry has role and content keys
    for entry in result:
        assert "role" in entry
        assert "content" in entry


@pytest.mark.asyncio
async def test_build_context_empty_tenant(db_session):
    tenant_id = uuid.uuid4()

    result = await build_context(db_session, tenant_id)

    assert result == []
