from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)
    
class MessageResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    sender_id: UUID
    content: str
    is_internal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)