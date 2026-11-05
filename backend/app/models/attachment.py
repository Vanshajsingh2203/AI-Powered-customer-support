import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.database.base import Base

class Attachment(Base):
    __tablename__="attachments"
    
    __table_args__=(
        Index("ix_attachments_ticket_id", "ticket_id"),
        Index("ix_attachments_message_id", "message_id"),
        Index("ix_attachments_uploaded_by", "uploaded_by"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False
    )
    
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ticket_messages.id", ondelete="SET NULL"),
        nullable=True
    )
    
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    ticket = relationship("Ticket", back_populates="attachments")
    message = relationship("TicketMessage", back_populates="attachments")
    uploader = relationship("User", back_populates="attachments")