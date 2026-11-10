
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)
    is_internal: bool = False


class MessageResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    sender_id: UUID
    content: str
    is_internal: bool
    created_at: datetime
    sender_name: str
    sender_role: str
    
    model_config = ConfigDict(from_attributes=True)
