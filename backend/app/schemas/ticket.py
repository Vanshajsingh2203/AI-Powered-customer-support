from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime

class TicketCreate(BaseModel):
    title : str = Field(min_length=5 , max_length=200)
    description: str = Field(min_length=10)

class TicketResponse(BaseModel):
    id:UUID
    title: str
    description: str
    status : str
    priority: str
    created_at: datetime
    updated_at: datetime
    
class TicketUpdate(BaseModel):
    title: str| None= Field(default = None, min_length = 5, max_length=200)
    description: str | None = Field(default = None , min_length=10)
    
    model_config = ConfigDict(from_attributes=True)