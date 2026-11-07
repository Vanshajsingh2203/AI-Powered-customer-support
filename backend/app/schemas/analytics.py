
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AgentWorkloadItem(BaseModel):
    agent_id: UUID
    agent_name: str
    active_tickets: int


class RecentTicketItem(BaseModel):
    ticket_id: UUID
    title: str
    status: str
    priority: str
    customer_name: str
    assigned_agent_name: str | None
    created_at: datetime


class AnalyticsOverviewResponse(BaseModel):
    total_tickets: int
    active_agents: int

    tickets_by_status: dict[str, int]
    tickets_by_priority: dict[str, int]

    average_closure_hours: float | None

    agent_workload: list[AgentWorkloadItem]
    recent_tickets: list[RecentTicketItem]
