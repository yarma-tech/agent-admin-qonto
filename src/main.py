import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import stripe
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket

from src.config import settings
from src.db import engine, get_db
from telegram import Update

bot_app = None
_health_check_task = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global bot_app, _health_check_task
    if settings.telegram_bot_token:
        from src.telegram.bot import create_bot_app, setup_webhook

        bot_app = create_bot_app()
        await bot_app.initialize()
        await setup_webhook(bot_app)

    from src.websocket.health import health_check_loop

    _health_check_task = asyncio.create_task(health_check_loop())

    yield

    if _health_check_task is not None:
        _health_check_task.cancel()
        try:
            await _health_check_task
        except asyncio.CancelledError:
            pass

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


@app.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
) -> dict[str, str]:
    from src.billing.webhooks import handle_stripe_webhook

    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    try:
        async for session in get_db():
            await handle_stripe_webhook(payload, stripe_signature, session)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "ok"}


@app.websocket("/ws/{tenant_id}")
async def websocket_proxy_endpoint(websocket: WebSocket, tenant_id: str) -> None:
    from src.websocket.server import websocket_endpoint

    await websocket_endpoint(websocket, tenant_id)
