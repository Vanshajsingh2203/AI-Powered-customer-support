"""Automatic ticket assignment.

This module is the only place that decides which agent an unassigned ticket
should go to. It is kept separate from the manual admin flow in
``app/services/assignment_service.py`` on purpose:

* a manual assignment always wins, and
* nothing in here ever touches a ticket that already has an agent.

The caller owns the transaction. These functions only ever ``flush()``, so the
assignment commits together with whatever the caller is already doing.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, nulls_first, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.models.user import User
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service


logger = logging.getLogger(__name__)

# Statuses that no longer occupy a slot in an agent's queue.
FINISHED_STATUSES = ("RESOLVED", "CLOSED")

# Value written to tickets.assignment_source by this module.
ASSIGNMENT_SOURCE_AUTO = "AUTO"


async def select_agent_for_assignment(
    db: AsyncSession,
) -> User | None:
    """Return the agent who should receive the next ticket, or None.

    Least-busy first: the active agent holding the fewest unfinished tickets.
    Ties are broken by whoever has gone longest without an assignment, and an
    agent who has never had one comes first, so when workloads are level the
    strategy behaves like round-robin. ``User.id`` is the final tie-break,
    which keeps the result deterministic.
    """

    # How many unfinished tickets each agent currently holds.
    open_ticket_counts = (
        select(
            Ticket.assigned_agent_id.label("agent_id"),
            func.count(Ticket.id).label("open_tickets"),
        )
        .where(
            Ticket.assigned_agent_id.is_not(None),
            Ticket.status.not_in(FINISHED_STATUSES),
        )
        .group_by(Ticket.assigned_agent_id)
        .subquery()
    )

    # When each agent was last given a ticket, automatically or manually.
    last_assignments = (
        select(
            TicketAssignment.agent_id.label("agent_id"),
            func.max(TicketAssignment.assigned_at).label("last_assigned_at"),
        )
        .group_by(TicketAssignment.agent_id)
        .subquery()
    )

    result = await db.execute(
        select(User)
        .outerjoin(
            open_ticket_counts,
            open_ticket_counts.c.agent_id == User.id,
        )
        .outerjoin(
            last_assignments,
            last_assignments.c.agent_id == User.id,
        )
        .where(
            User.role == "AGENT",
            User.is_active.is_(True),
        )
        .order_by(
            func.coalesce(open_ticket_counts.c.open_tickets, 0).asc(),
            nulls_first(last_assignments.c.last_assigned_at.asc()),
            User.id.asc(),
        )
        .limit(1)
    )

    return result.scalar_one_or_none()


async def auto_assign_ticket(
    db: AsyncSession,
    ticket_id: UUID,
) -> Ticket | None:
    """Assign a still-unassigned ticket to an agent automatically.

    Returns the updated ticket, or ``None`` when nothing was assigned. That
    happens when the ticket does not exist, already has an agent, or no active
    agent is available. Callers can safely ignore the return value: a ticket
    that cannot be auto-assigned is left exactly as it was, waiting for an
    admin to assign it manually.
    """

    # 1. Lock the ticket so two concurrent callers cannot both assign it.
    result = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .with_for_update()
    )

    ticket = result.scalar_one_or_none()

    if ticket is None:
        return None

    # 2. Never override an existing assignment. This single check is what
    #    keeps a manual admin assignment safe from the automation, no matter
    #    how often or from where this function is called.
    if ticket.assigned_agent_id is not None:
        return None

    # 3. Choose an agent.
    agent = await select_agent_for_assignment(db)

    if agent is None:
        logger.warning(
            "No active agent available to auto-assign ticket %s",
            ticket_id,
        )

        return None

    # 4. Close any stale active history row before inserting a new one, so the
    #    "one active assignment per ticket" index can never be violated.
    result = await db.execute(
        select(TicketAssignment).where(
            TicketAssignment.ticket_id == ticket.id,
            TicketAssignment.unassigned_at.is_(None),
        )
    )

    stale_assignment = result.scalar_one_or_none()

    if stale_assignment is not None:
        stale_assignment.unassigned_at = datetime.now(timezone.utc)

    # 5. Record the assignment in the history table. assigned_by is NULL
    #    because no user performed this assignment.
    db.add(
        TicketAssignment(
            ticket_id=ticket.id,
            agent_id=agent.id,
            assigned_by=None,
        )
    )

    # 6. Point the ticket at the agent and record how it got there.
    ticket.assigned_agent_id = agent.id
    ticket.assignment_source = ASSIGNMENT_SOURCE_AUTO

    # 7. Notify the agent, exactly as the manual flow does.
    await notification_service.create_notification(
        db=db,
        user_id=agent.id,
        ticket_id=ticket.id,
        title="New ticket assigned",
        message=(
            f"Ticket '{ticket.title}' was automatically assigned to you. "
            "Please review it."
        ),
        notification_type="TICKET_ASSIGNED",
    )

    # 8. Leave a trace showing the system, not a person, did this.
    await audit_service.create_log(
        db=db,
        user_id=None,
        ticket_id=ticket.id,
        action="TICKET_AUTO_ASSIGNED",
        old_value={"assigned_agent_id": None},
        new_value={
            "assigned_agent_id": str(agent.id),
            "assignment_source": ASSIGNMENT_SOURCE_AUTO,
        },
    )

    await db.flush()

    return ticket
