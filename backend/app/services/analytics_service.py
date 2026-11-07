
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    AgentWorkloadItem,
    RecentTicketItem,
)


class AnalyticsService:

    async def get_overview(
        self,
        db: AsyncSession,
    ) -> AnalyticsOverviewResponse:

        # 1. Total tickets
        total_result = await db.execute(
            select(func.count(Ticket.id))
        )
        total_tickets = total_result.scalar_one()

        # 2. Count tickets by status
        status_result = await db.execute(
            select(
                Ticket.status,
                func.count(Ticket.id)
            )
            .group_by(Ticket.status)
        )

        status_counts = {
            "OPEN": 0,
            "IN_PROGRESS": 0,
            "WAITING_ON_CUSTOMER": 0,
            "RESOLVED": 0,
            "CLOSED": 0,
        }

        for status_name, count in status_result.all():
            status_counts[status_name] = count

        # 3. Count tickets by priority
        priority_result = await db.execute(
            select(
                Ticket.priority,
                func.count(Ticket.id)
            )
            .group_by(Ticket.priority)
        )

        priority_counts = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "URGENT": 0,
        }

        for priority_name, count in priority_result.all():
            priority_counts[priority_name] = count

        # 4. Count active agents
        active_agents_result = await db.execute(
            select(func.count(User.id)).where(
                User.role == "AGENT",
                User.is_active.is_(True),
            )
        )

        active_agents = active_agents_result.scalar_one()

        # 5. Calculate active ticket workload per agent
        workload_result = await db.execute(
            select(
                User.id,
                User.full_name,
                func.count(Ticket.id),
            )
            .select_from(User)
            .outerjoin(
                Ticket,
                and_(
                    Ticket.assigned_agent_id == User.id,
                    Ticket.status.in_([
                        "OPEN",
                        "IN_PROGRESS",
                        "WAITING_ON_CUSTOMER",
                    ]),
                ),
            )
            .where(
                User.role == "AGENT",
                User.is_active.is_(True),
            )
            .group_by(User.id, User.full_name)
            .order_by(func.count(Ticket.id).desc())
        )

        agent_workload = [
            AgentWorkloadItem(
                agent_id=agent_id,
                agent_name=agent_name,
                active_tickets=count,
            )
            for agent_id, agent_name, count in workload_result.all()
        ]

        # 6. Calculate average closure time in hours
        closure_result = await db.execute(
            select(
                func.avg(
                    extract(
                        "epoch",
                        Ticket.closed_at - Ticket.created_at,
                    )
                ) / 3600.0
            )
            .where(Ticket.closed_at.is_not(None))
        )

        average_closure_hours = closure_result.scalar_one()

        if average_closure_hours is not None:
            average_closure_hours = float(average_closure_hours)

        # 7. Get the five most recently created tickets
        Customer = aliased(User)
        Agent = aliased(User)

        recent_result = await db.execute(
            select(
                Ticket.id,
                Ticket.title,
                Ticket.status,
                Ticket.priority,
                Customer.full_name,
                Agent.full_name,
                Ticket.created_at,
            )
            .select_from(Ticket)
            .join(
                Customer,
                Ticket.customer_id == Customer.id,
            )
            .outerjoin(
                Agent,
                Ticket.assigned_agent_id == Agent.id,
            )
            .order_by(Ticket.created_at.desc())
            .limit(5)
        )

        recent_tickets = [
            RecentTicketItem(
                ticket_id=row[0],
                title=row[1],
                status=row[2],
                priority=row[3],
                customer_name=row[4],
                assigned_agent_name=row[5],
                created_at=row[6],
            )
            for row in recent_result.all()
        ]

        return AnalyticsOverviewResponse(
            total_tickets=total_tickets,
            active_agents=active_agents,
            tickets_by_status=status_counts,
            tickets_by_priority=priority_counts,
            average_closure_hours=average_closure_hours,
            agent_workload=agent_workload,
            recent_tickets=recent_tickets,
        )


analytics_service = AnalyticsService()
