"""Agent tools for saving and searching business memory."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.rag.indexer import index_text
from src.rag.search import search_memory


async def save_memo(session: AsyncSession, tenant_id: uuid.UUID, text: str) -> str:
    """Embed and persist *text* in the tenant's vector memory."""
    await index_text(session, tenant_id, text)
    return "Memo sauvegardé."


async def search_memo(session: AsyncSession, tenant_id: uuid.UUID, query: str) -> list[str]:
    """Return the top 5 memory entries semantically closest to *query*."""
    return await search_memory(session, tenant_id, query, limit=5)
