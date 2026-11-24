"""Tests for automatic ticket assignment.

Three guarantees matter here:

(a) manual admin assignment keeps working exactly as before,
(b) a new unassigned ticket is auto-assigned to the right agent,
(c) auto-assignment never overrides a ticket an admin assigned.
"""

import uuid

import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.services.auto_assignment import auto_assign_ticket


DESCRIPTION = "A sufficiently detailed description for an auto-assignment test."


async def create_ticket(client, auth_headers, customer, title="Auto assignment ticket"):
    """Create a ticket through the public customer endpoint."""

    response = await client.post(
        "/api/v1/tickets/",
        headers=auth_headers(customer),
        json={"title": title, "description": DESCRIPTION},
    )

    assert response.status_code == 201, response.text

    return response.json()


async def add_ticket_directly(db_session, customer, agent=None, status="OPEN"):
    """Insert a ticket straight into the database to set up agent workload."""

    ticket = Ticket(
        title="Pre-existing workload ticket",
        description=DESCRIPTION,
        customer_id=customer.id,
        assigned_agent_id=agent.id if agent else None,
        assignment_source="ADMIN" if agent else None,
        status=status,
        priority="MEDIUM",
    )

    db_session.add(ticket)
    await db_session.flush()

    return ticket


async def reload_ticket(db_session, ticket_id):
    result = await db_session.execute(
        select(Ticket).where(Ticket.id == uuid.UUID(str(ticket_id)))
    )

    return result.scalar_one()


# ---------------------------------------------------------------------------
# (b) New unassigned tickets get auto-assigned
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_new_ticket_is_auto_assigned_to_the_active_agent(
    client, user_factory, auth_headers
):
    agent = await user_factory(role="AGENT")
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] == str(agent.id)
    assert ticket["assignment_source"] == "AUTO"
    assert ticket["assigned_agent_name"] == agent.full_name


@pytest.mark.asyncio
async def test_auto_assignment_records_history_notification_and_audit_log(
    client, user_factory, auth_headers, db_session
):
    agent = await user_factory(role="AGENT")
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)
    ticket_id = uuid.UUID(ticket["id"])

    # History row exists, and assigned_by is NULL because no user did it.
    assignments = await db_session.execute(
        select(TicketAssignment).where(
            TicketAssignment.ticket_id == ticket_id
        )
    )

    history = assignments.scalars().all()

    assert len(history) == 1
    assert history[0].agent_id == agent.id
    assert history[0].assigned_by is None
    assert history[0].unassigned_at is None

    # The agent is notified, just as in the manual flow.
    notifications = await db_session.execute(
        select(Notification).where(
            Notification.user_id == agent.id,
            Notification.ticket_id == ticket_id,
        )
    )

    assert len(notifications.scalars().all()) == 1

    # The audit trail shows the system, not a person, made the assignment.
    logs = await db_session.execute(
        select(AuditLog).where(
            AuditLog.ticket_id == ticket_id,
            AuditLog.action == "TICKET_AUTO_ASSIGNED",
        )
    )

    log = logs.scalar_one()

    assert log.user_id is None
    assert log.new_value["assigned_agent_id"] == str(agent.id)


@pytest.mark.asyncio
async def test_auto_assignment_picks_the_least_busy_agent(
    client, user_factory, auth_headers, db_session
):
    busy_agent = await user_factory(role="AGENT", full_name="Busy Agent")
    free_agent = await user_factory(role="AGENT", full_name="Free Agent")
    customer = await user_factory(role="CUSTOMER")

    # Give one agent a queue of open work.
    await add_ticket_directly(db_session, customer, busy_agent)
    await add_ticket_directly(db_session, customer, busy_agent)

    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] == str(free_agent.id)


@pytest.mark.asyncio
async def test_resolved_and_closed_tickets_do_not_count_as_workload(
    client, user_factory, auth_headers, db_session
):
    finished_agent = await user_factory(role="AGENT", full_name="Finished Agent")
    working_agent = await user_factory(role="AGENT", full_name="Working Agent")
    customer = await user_factory(role="CUSTOMER")

    # Three tickets, but all of them are off this agent's plate.
    await add_ticket_directly(db_session, customer, finished_agent, status="RESOLVED")
    await add_ticket_directly(db_session, customer, finished_agent, status="CLOSED")
    await add_ticket_directly(db_session, customer, finished_agent, status="CLOSED")

    # One ticket, but it is still open.
    await add_ticket_directly(db_session, customer, working_agent, status="OPEN")

    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] == str(finished_agent.id)


@pytest.mark.asyncio
async def test_equal_workload_rotates_between_agents(
    client, user_factory, auth_headers
):
    await user_factory(role="AGENT", full_name="First Agent")
    await user_factory(role="AGENT", full_name="Second Agent")
    customer = await user_factory(role="CUSTOMER")

    first = await create_ticket(client, auth_headers, customer, title="First ticket")
    second = await create_ticket(client, auth_headers, customer, title="Second ticket")

    # Both agents start idle, so the second ticket must go to the other one.
    assert first["assigned_agent_id"] != second["assigned_agent_id"]
    assert first["assignment_source"] == "AUTO"
    assert second["assignment_source"] == "AUTO"


@pytest.mark.asyncio
async def test_inactive_agents_are_never_auto_assigned(
    client, user_factory, auth_headers
):
    inactive_agent = await user_factory(role="AGENT", is_active=False)
    active_agent = await user_factory(role="AGENT")
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] == str(active_agent.id)
    assert ticket["assigned_agent_id"] != str(inactive_agent.id)


@pytest.mark.asyncio
async def test_customers_and_admins_are_never_auto_assigned(
    client, user_factory, auth_headers
):
    await user_factory(role="ADMIN")
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)

    # Only agents can receive tickets, so this one stays unassigned.
    assert ticket["assigned_agent_id"] is None
    assert ticket["assignment_source"] is None


@pytest.mark.asyncio
async def test_ticket_creation_still_succeeds_with_no_agents_available(
    client, user_factory, auth_headers
):
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)

    # Creation must not fail just because nobody is available to take it.
    assert ticket["status"] == "OPEN"
    assert ticket["assigned_agent_id"] is None
    assert ticket["assignment_source"] is None


@pytest.mark.asyncio
async def test_only_inactive_agents_leaves_the_ticket_unassigned(
    client, user_factory, auth_headers
):
    await user_factory(role="AGENT", is_active=False)
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] is None
    assert ticket["assignment_source"] is None


# ---------------------------------------------------------------------------
# (a) Manual assignment still works unchanged
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manual_assignment_still_works_on_an_unassigned_ticket(
    client, user_factory, auth_headers, db_session
):
    # No agent exists yet, so this ticket is created unassigned.
    customer = await user_factory(role="CUSTOMER")
    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] is None

    admin = await user_factory(role="ADMIN")
    agent = await user_factory(role="AGENT")

    response = await client.post(
        f"/api/v1/agents/tickets/{ticket['id']}/assign",
        headers=auth_headers(admin),
        json={"agent_id": str(agent.id)},
    )

    assert response.status_code == 201, response.text
    assert response.json()["agent_id"] == str(agent.id)
    assert response.json()["assigned_by"] == str(admin.id)

    stored = await reload_ticket(db_session, ticket["id"])

    assert stored.assigned_agent_id == agent.id
    assert stored.assignment_source == "ADMIN"


@pytest.mark.asyncio
async def test_admin_can_reassign_an_auto_assigned_ticket(
    client, user_factory, auth_headers, db_session
):
    auto_agent = await user_factory(role="AGENT", full_name="Auto Agent")
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] == str(auto_agent.id)
    assert ticket["assignment_source"] == "AUTO"

    admin = await user_factory(role="ADMIN")
    chosen_agent = await user_factory(role="AGENT", full_name="Chosen Agent")

    response = await client.post(
        f"/api/v1/agents/tickets/{ticket['id']}/assign",
        headers=auth_headers(admin),
        json={"agent_id": str(chosen_agent.id)},
    )

    assert response.status_code == 201, response.text

    stored = await reload_ticket(db_session, ticket["id"])

    assert stored.assigned_agent_id == chosen_agent.id
    assert stored.assignment_source == "ADMIN"

    # The automatic history row is closed, the manual one is active.
    assignments = await db_session.execute(
        select(TicketAssignment)
        .where(TicketAssignment.ticket_id == stored.id)
        .order_by(TicketAssignment.assigned_at)
    )

    history = assignments.scalars().all()

    assert len(history) == 2

    automatic_row = next(row for row in history if row.agent_id == auto_agent.id)
    manual_row = next(row for row in history if row.agent_id == chosen_agent.id)

    assert automatic_row.unassigned_at is not None
    assert manual_row.unassigned_at is None
    assert manual_row.assigned_by == admin.id


@pytest.mark.asyncio
async def test_admin_confirming_the_auto_assigned_agent_makes_it_manual(
    client, user_factory, auth_headers, db_session
):
    agent = await user_factory(role="AGENT")
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] == str(agent.id)

    admin = await user_factory(role="ADMIN")

    # The admin assigns the ticket to the agent who already has it.
    response = await client.post(
        f"/api/v1/agents/tickets/{ticket['id']}/assign",
        headers=auth_headers(admin),
        json={"agent_id": str(agent.id)},
    )

    assert response.status_code == 201, response.text
    assert response.json()["assigned_by"] == str(admin.id)

    stored = await reload_ticket(db_session, ticket["id"])

    assert stored.assignment_source == "ADMIN"

    # No duplicate history row was created.
    assignments = await db_session.execute(
        select(TicketAssignment).where(
            TicketAssignment.ticket_id == stored.id
        )
    )

    assert len(assignments.scalars().all()) == 1


@pytest.mark.asyncio
async def test_manual_assignment_still_rejects_an_inactive_agent(
    client, user_factory, auth_headers
):
    customer = await user_factory(role="CUSTOMER")
    ticket = await create_ticket(client, auth_headers, customer)

    admin = await user_factory(role="ADMIN")
    inactive_agent = await user_factory(role="AGENT", is_active=False)

    response = await client.post(
        f"/api/v1/agents/tickets/{ticket['id']}/assign",
        headers=auth_headers(admin),
        json={"agent_id": str(inactive_agent.id)},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_manual_assignment_is_still_admin_only(
    client, user_factory, auth_headers
):
    agent = await user_factory(role="AGENT")
    customer = await user_factory(role="CUSTOMER")
    ticket = await create_ticket(client, auth_headers, customer)

    response = await client.post(
        f"/api/v1/agents/tickets/{ticket['id']}/assign",
        headers=auth_headers(agent),
        json={"agent_id": str(agent.id)},
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# (c) Auto-assignment never overrides a manual assignment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_assignment_does_not_touch_a_manually_assigned_ticket(
    client, user_factory, auth_headers, db_session
):
    customer = await user_factory(role="CUSTOMER")
    ticket = await create_ticket(client, auth_headers, customer)

    admin = await user_factory(role="ADMIN")
    manual_agent = await user_factory(role="AGENT", full_name="Manual Agent")

    assigned = await client.post(
        f"/api/v1/agents/tickets/{ticket['id']}/assign",
        headers=auth_headers(admin),
        json={"agent_id": str(manual_agent.id)},
    )

    assert assigned.status_code == 201

    # A completely idle agent exists, so a naive implementation would move the
    # ticket. Auto-assignment must refuse instead.
    await user_factory(role="AGENT", full_name="Idle Agent")

    result = await auto_assign_ticket(
        db=db_session,
        ticket_id=uuid.UUID(ticket["id"]),
    )

    assert result is None

    stored = await reload_ticket(db_session, ticket["id"])

    assert stored.assigned_agent_id == manual_agent.id
    assert stored.assignment_source == "ADMIN"


@pytest.mark.asyncio
async def test_auto_assignment_is_a_no_op_on_an_auto_assigned_ticket(
    client, user_factory, auth_headers, db_session
):
    first_agent = await user_factory(role="AGENT", full_name="First Agent")
    customer = await user_factory(role="CUSTOMER")

    ticket = await create_ticket(client, auth_headers, customer)

    assert ticket["assigned_agent_id"] == str(first_agent.id)

    # Running it again must not reshuffle the ticket onto a newer, idler agent.
    await user_factory(role="AGENT", full_name="Later Agent")

    result = await auto_assign_ticket(
        db=db_session,
        ticket_id=uuid.UUID(ticket["id"]),
    )

    assert result is None

    stored = await reload_ticket(db_session, ticket["id"])

    assert stored.assigned_agent_id == first_agent.id

    assignments = await db_session.execute(
        select(TicketAssignment).where(
            TicketAssignment.ticket_id == stored.id
        )
    )

    assert len(assignments.scalars().all()) == 1


@pytest.mark.asyncio
async def test_auto_assignment_returns_none_for_a_missing_ticket(db_session):
    result = await auto_assign_ticket(
        db=db_session,
        ticket_id=uuid.uuid4(),
    )

    assert result is None
