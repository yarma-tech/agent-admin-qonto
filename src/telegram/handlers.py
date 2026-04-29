import anthropic
from telegram.ext import ContextTypes

from src.agent.loop import run_agent
from src.agent.tools.transcribe import transcribe_voice
from src.config import settings
from src.db import async_session_factory
from src.rag.entity_detector import should_index
from src.rag.indexer import index_text
from src.telegram.auth import get_or_create_tenant
from telegram import Update


async def process_voice_memo(session, tenant_id, transcription: str) -> str | None:
    """Process transcription as a business memo. Returns confirmatory summary or None."""
    if not should_index(transcription):
        return None

    # Index in RAG
    await index_text(session, tenant_id, transcription)

    # Generate confirmatory summary
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=(
            "Tu résumes des memos vocaux business en une phrase confirmative courte commençant par 'Note :'. "
            "Si une info critique est ambiguë (ex: TTC ou HT?), ajoute une question."
        ),
        messages=[{"role": "user", "content": f"Résume ce memo : {transcription}"}],
    )
    return response.content[0].text


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

        # Try memo pipeline first
        memo_summary = await process_voice_memo(session, tenant.id, text)
        if memo_summary:
            await context.bot.send_message(chat_id=chat_id, text=memo_summary)
            return

        # If not a memo, treat as regular command → agent loop
        response = await run_agent(session, tenant.id, text)

    await context.bot.send_message(chat_id=chat_id, text=response)
