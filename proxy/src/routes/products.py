from typing import Any

from fastapi import APIRouter, Depends

from src.auth import verify_token
from src.qonto_client import api_fetch

router = APIRouter(prefix="/products", tags=["products"], dependencies=[Depends(verify_token)])


@router.post("/")
async def create_product(body: dict[str, Any]) -> dict:
    return await api_fetch("POST", "/products", body=body)


@router.get("/")
async def list_products() -> dict:
    return await api_fetch("GET", "/products")
