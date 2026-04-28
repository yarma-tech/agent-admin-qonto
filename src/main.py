from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from src.config import settings
from src.db import engine
from telegram import Update

bot_app = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global bot_app
    if settings.telegram_bot_token:
        from src.telegram.bot import create_bot_app, setup_webhook

        bot_app = create_bot_app()
        await bot_app.initialize()
        await setup_webhook(bot_app)

    yield

    if bot_app is not None:
        await bot_app.shutdown()
    await engine.dispose()


app = FastAPI(title="Agent Qonto", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> dict[str, str]:
    if bot_app is None:
        return {"status": "bot not configured"}
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}
