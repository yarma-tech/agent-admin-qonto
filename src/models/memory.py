"""MemoryEmbedding model — stores pgvector embeddings per tenant."""

import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.tenant import Base


class MemoryEmbedding(Base):
    __tablename__ = "memory_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))  # OpenAI text-embedding-3-small dimension
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
