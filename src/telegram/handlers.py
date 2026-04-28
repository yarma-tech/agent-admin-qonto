from telegram.ext import ContextTypes

from src.agent.loop import run_agent
from src.agent.tools.transcribe import transcribe_voice
from src.db import async_session_factory
from src.telegram.auth import get_or_create_tenant
from telegram import Update


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    first_name = update.effective_user.first_name if update.effective_user else "inconnu"
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Bienvenue {first_name} ! Je suis ton assistant Qonto. Envoie-moi un message texte ou vocal.",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return

    text = update.message.text or ""
    chat_id = update.effective_chat.id

    async with async_session_factory() as session:
        tenant, _user = await get_or_create_tenant(
            session,
            update.effective_user.id,
            update.effective_user.first_name or "inconnu",
        )
        response = await run_agent(session, tenant.id, text)

    await context.bot.send_message(chat_id=chat_id, text=response)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    chat_id = update.effective_chat.id
    file = await context.bot.get_file(voice.file_id)
    audio_bytes = await file.download_as_bytearray()
    text = await transcribe_voice(bytes(audio_bytes))

    async with async_session_factory() as session:
        tenant, _user = await get_or_create_tenant(
            session,
            update.effective_user.id,
            update.effective_user.first_name or "inconnu",
        )
        response = await run_agent(session, tenant.id, text)

    await context.bot.send_message(chat_id=chat_id, text=response)
