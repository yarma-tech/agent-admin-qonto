from fastapi import APIRouter

from src.qonto_client import api_fetch

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    """Return proxy status and whether the Qonto credentials are valid."""
    qonto_connected = False
    try:
        await api_fetch("GET", "/organization")
        qonto_connected = True
    except Exception:
        pass

    return {"status": "ok", "qonto_connected": qonto_connected}
