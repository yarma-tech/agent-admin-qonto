"""WebSocket message protocol for cloud <-> proxy communication."""

from typing import Any

from pydantic import BaseModel


class WSCommand(BaseModel):
    id: str  # Request ID for correlation
    method: str  # GET, POST, PATCH, PUT, DELETE
    endpoint: str  # e.g. /quotes
    body: dict | None = None
    query: dict | None = None


class WSResponse(BaseModel):
    id: str
    status: int
    data: Any = None
    error: str | None = None
