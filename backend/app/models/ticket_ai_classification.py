import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, CheckConstraint, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TicketAIClassification(Base):
    __tablename__ = "ticket_ai_classifications"

    __table_args__ = (
        CheckConstraint(
            "sentiment IN ('POSITIVE', 'NEUTRAL', 'NEGATIVE', 'FRUSTRATED')",
            name="check_ticket_ai_classification_sentiment",
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="check_ticket_ai_classification_confidence",
        ),
        Index("ix_ticket_ai_classifications_ticket_id", "ticket_id", unique=True),
        Index("ix_ticket_ai_classifications_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )

    sentiment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ticket = relationship(
        "Ticket",
        back_populates="ai_classification",
    )