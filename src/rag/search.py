"""Semantic search over the tenant's vector memory."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.memory import MemoryEmbedding
from src.rag.embeddings import generate_embedding


async def search_memory(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    query: str,
    limit: int = 5,
) -> list[str]:
    """Return the *limit* most similar memory contents to *query* for *tenant_id*."""
    query_embedding = await generate_embedding(query)
    stmt = (
        select(MemoryEmbedding.content)
        .where(MemoryEmbedding.tenant_id == tenant_id)
        .order_by(MemoryEmbedding.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [row[0] for row in result.all()]
