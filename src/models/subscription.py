import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.tenant import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), unique=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(20))  # "solo" | "pro"
    status: Mapped[str] = mapped_column(String(20))  # "active" | "paused" | "canceled"
    actions_used: Mapped[int] = mapped_column(Integer, default=0)
    actions_limit: Mapped[int] = mapped_column(Integer, default=50)  # Solo=50, Pro=-1 (unlimited)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
