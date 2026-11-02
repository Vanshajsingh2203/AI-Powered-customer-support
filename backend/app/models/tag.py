
import uuid

from sqlalchemy import String, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Tag(Base):
    __tablename__ = "tags"

    __table_args__ = (
        Index(
            "uq_tags_name_lower",
            text("lower(name)"),
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    tickets = relationship(
    "Ticket",
    secondary="ticket_tags",
    back_populates="tags",
)