from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.config import settings
from src.telegram.handlers import handle_message, handle_start, handle_voice


def create_bot_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    return app


async def setup_webhook(app: Application) -> None:
    webhook_url = f"{settings.webhook_base_url}/telegram/webhook"
    await app.bot.set_webhook(url=webhook_url)
