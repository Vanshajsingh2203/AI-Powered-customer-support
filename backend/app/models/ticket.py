from app.database.base import Base
import uuid
from datetime import datetime , timezone

from sqlalchemy import String, Text , DateTime , ForeignKey, CheckConstraint , Index

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Ticket(Base):
    __tablename__ = "tickets"
    
    __table_args__= (
        CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'WAITING_ON_CUSTOMER', 'RESOLVED', 'CLOSED')",
            name = "check_ticket_status",
        ),
        CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')",
            name="check_ticket_priority",
        ),
        
        Index("ix_tickets_customer_id", "customer_id"),
        Index("ix_tickets_assigned_agent_id", "assigned_agent_id"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_created_at", "created_at"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default= uuid.uuid4,
    )
    
    title: Mapped[str] = mapped_column(
        String(200),
        nullable= False,
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    status: Mapped[str] = mapped_column(
        String(30),
        default="OPEN",
        server_default="OPEN",
        nullable=False,
    )
    
    priority: Mapped[str] = mapped_column(
        String(20),
        default="MEDIUM",
        server_default="MEDIUM",
        nullable=False,
    )
    
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    customer = relationship(
        "User",
        foreign_keys=[customer_id],
        back_populates="created_tickets",
    )
    
    assigned_agent = relationship(
        "User",
        foreign_keys=[assigned_agent_id],
        back_populates="assigned_tickets",
    )
    
    messages = relationship(
    "TicketMessage",
    foreign_keys="TicketMessage.ticket_id",
    back_populates="ticket",
    cascade="all, delete-orphan",
    )
        
    category = relationship(
    "Category",
    back_populates="tickets",
    )
    
    category_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("categories.id", ondelete="SET NULL"),
    nullable=True,
    )

    tags = relationship(
    "Tag",
    secondary="ticket_tags",
    back_populates="tickets",   
    )

    assignments = relationship(
    "TicketAssignment",
    back_populates="ticket",
    cascade="all, delete-orphan",
    )
    
    audit_logs = relationship(
    "AuditLog",
    back_populates="ticket",
    )
    notifications = relationship(
    "Notification",
    back_populates="ticket",
    )