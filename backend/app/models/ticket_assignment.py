
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"

    __table_args__ = (
        Index(
            "uq_ticket_active_assignment",
            "ticket_id",
            unique=True,
            postgresql_where=text("unassigned_at IS NULL"),
        ),
        Index("ix_ticket_assignments_agent_id", "agent_id"),
        Index("ix_ticket_assignments_assigned_by", "assigned_by"),
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

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    assigned_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    unassigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ticket = relationship(
        "Ticket",
        back_populates="assignments",
    )

    agent = relationship(
        "User",
        foreign_keys=[agent_id],
        back_populates="received_assignments",
    )

    assigner = relationship(
        "User",
        foreign_keys=[assigned_by],
        back_populates="created_assignments",
    )

    