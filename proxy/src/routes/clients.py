from typing import Any

from fastapi import APIRouter, Depends

from src.auth import verify_token
from src.qonto_client import api_fetch

router = APIRouter(prefix="/clients", tags=["clients"], dependencies=[Depends(verify_token)])


@router.post("/")
async def create_client(body: dict[str, Any]) -> dict:
    return await api_fetch("POST", "/clients", body=body)


@router.get("/")
async def list_clients() -> dict:
    return await api_fetch("GET", "/clients")


@router.get("/{client_id}")
async def get_client(client_id: str) -> dict:
    return await api_fetch("GET", f"/clients/{client_id}")


@router.patch("/{client_id}")
async def update_client(client_id: str, body: dict[str, Any]) -> dict:
    return await api_fetch("PATCH", f"/clients/{client_id}", body=body)
