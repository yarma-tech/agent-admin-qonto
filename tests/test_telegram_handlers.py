import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram.handlers import handle_message, handle_start

FAKE_TENANT_ID = uuid.uuid4()


def _make_fake_tenant():
    tenant = MagicMock()
    tenant.id = FAKE_TENANT_ID
    return tenant


@pytest.mark.asyncio
async def test_start_sends_welcome() -> None:
    update = MagicMock()
    update.effective_user.first_name = "Test"
    update.effective_chat.id = 123
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await handle_start(update, context)

    context.bot.send_message.assert_called_once()
    call_kwargs = context.bot.send_message.call_args.kwargs
    assert "Bienvenue" in call_kwargs["text"]
    assert "Test" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_start_sends_to_correct_chat() -> None:
    update = MagicMock()
    update.effective_user.first_name = "Alice"
    update.effective_chat.id = 456
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await handle_start(update, context)

    call_kwargs = context.bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 456


@pytest.mark.asyncio
async def test_start_welcome_contains_assistant_mention() -> None:
    update = MagicMock()
    update.effective_user.first_name = "Bob"
    update.effective_chat.id = 789
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await handle_start(update, context)

    call_kwargs = context.bot.send_message.call_args.kwargs
    assert "assistant Qonto" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_handle_message_calls_agent_and_replies() -> None:
    update = MagicMock()
    update.message.text = "Bonjour"
    update.effective_chat.id = 123
    update.effective_user.id = 42
    update.effective_user.first_name = "Alice"
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    fake_tenant = _make_fake_tenant()
    fake_user = MagicMock()

    with (
        patch("src.telegram.handlers.get_or_create_tenant", new=AsyncMock(return_value=(fake_tenant, fake_user))),
        patch("src.telegram.handlers.run_agent", new=AsyncMock(return_value="Réponse agent")),
        patch("src.telegram.handlers.async_session_factory") as mock_factory,
    ):
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        await handle_message(update, context)

    context.bot.send_message.assert_called_once()
    call_kwargs = context.bot.send_message.call_args.kwargs
    assert call_kwargs["text"] == "Réponse agent"


@pytest.mark.asyncio
async def test_handle_message_sends_to_correct_chat() -> None:
    update = MagicMock()
    update.message.text = "Hello"
    update.effective_chat.id = 999
    update.effective_user.id = 7
    update.effective_user.first_name = "Bob"
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    fake_tenant = _make_fake_tenant()
    fake_user = MagicMock()

    with (
        patch("src.telegram.handlers.get_or_create_tenant", new=AsyncMock(return_value=(fake_tenant, fake_user))),
        patch("src.telegram.handlers.run_agent", new=AsyncMock(return_value="OK")),
        patch("src.telegram.handlers.async_session_factory") as mock_factory,
    ):
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        await handle_message(update, context)

    call_kwargs = context.bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999
