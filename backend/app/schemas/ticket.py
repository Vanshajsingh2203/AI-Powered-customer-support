from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Literal

class TicketCreate(BaseModel):
    title : str = Field(min_length=5 , max_length=200)
    description: str = Field(min_length=10)
    category_id: UUID | None = None
    
class TicketResponse(BaseModel):
    id:UUID
    title: str
    description: str
    status : str
    priority: str
    created_at: datetime
    updated_at: datetime
    category_id: UUID | None = None
    category_name: str | None = None
    assigned_agent_id: UUID | None = None
    assigned_agent_name: str | None = None
    customer_name: str
    customer_email: str
    
    model_config = ConfigDict(from_attributes=True)
    
    
class TicketUpdate(BaseModel):
    title: str| None= Field(default = None, min_length = 5, max_length=200)
    description: str | None = Field(default = None , min_length=10)
    
    model_config = ConfigDict(from_attributes=True)
    
class TicketAssign(BaseModel):
    agent_id: UUID
    
class TicketAssignmentResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    agent_id: UUID
    assigned_by: UUID
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class TicketAgentUpdate(BaseModel):
    status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "WAITING_ON_CUSTOMER",
        "RESOLVED",
        "CLOSED",
    ] | None = None

    priority: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "URGENT",
    ] | None = None

    model_config = ConfigDict(extra="forbid")
    
class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    