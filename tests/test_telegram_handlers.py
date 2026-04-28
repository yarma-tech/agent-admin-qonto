from unittest.mock import AsyncMock, MagicMock

import pytest

from src.telegram.handlers import handle_message, handle_start


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
async def test_handle_message_echoes_text() -> None:
    update = MagicMock()
    update.message.text = "Bonjour"
    update.effective_chat.id = 123
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await handle_message(update, context)

    context.bot.send_message.assert_called_once()
    call_kwargs = context.bot.send_message.call_args.kwargs
    assert "Recu" in call_kwargs["text"]
    assert "Bonjour" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_handle_message_sends_to_correct_chat() -> None:
    update = MagicMock()
    update.message.text = "Hello"
    update.effective_chat.id = 999
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await handle_message(update, context)

    call_kwargs = context.bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999
