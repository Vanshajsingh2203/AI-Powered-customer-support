import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean , DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped , mapped_column

from app.database.base import Base

class User(Base):
    __tablename__ = "users"
    
    __table_args__ = (
    CheckConstraint(
        "role IN ('CUSTOMER', 'AGENT', 'ADMIN')",
        name="check_user_role"
        ),
    )
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key= True,
        default=uuid.uuid4
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable= False,
        index= True
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    
    role: Mapped[str] = mapped_column(
        String(20),
        default="CUSTOMER",
        server_default="CUSTOMER",
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )