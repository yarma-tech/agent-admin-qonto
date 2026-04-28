"""Index a text chunk into the vector memory for a given tenant."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.memory import MemoryEmbedding
from src.rag.embeddings import generate_embedding


async def index_text(session: AsyncSession, tenant_id: uuid.UUID, text: str) -> None:
    """Embed *text* and persist it as a MemoryEmbedding for *tenant_id*."""
    embedding = await generate_embedding(text)
    memory = MemoryEmbedding(tenant_id=tenant_id, content=text, embedding=embedding)
    session.add(memory)
    await session.commit()
